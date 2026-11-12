
import json
from typing import Any, Dict, Optional
from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.database_models import IdempotencyRecordDB
from app.repositories.interfaces import IdempotencyRepositoryProtocol


class PostgresIdempotencyRepository(IdempotencyRepositoryProtocol):
    """
    PostgreSQL-backed implementation of the idempotency repository.

    Records allow completed requests to be recognized across application
    instances and process restarts.

    The repository does not commit or roll back transactions. The caller
    owns transaction boundaries.

    A transaction-scoped PostgreSQL advisory lock serializes requests that
    share a key. The completed replay record is committed in the same
    transaction as the payment mutation. A unique database constraint
    remains the final safeguard against duplicate records.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def claim(self, idempotency_key: str) -> None:
        """
        Acquire a transaction-scoped lock for one idempotency key.

        Requests using the same key serialize until the caller commits or
        rolls back. The completed payment mutation and its replay record are
        therefore observed together by the next request.
        """
        if not idempotency_key or not idempotency_key.strip():
            raise ValueError("Idempotency key must not be empty.")

        if len(idempotency_key) > 255:
            raise ValueError(
                "Idempotency key must be 255 characters or fewer."
            )

        lock_key = f"payguard-ai:idempotency:{idempotency_key}"
        self.db.execute(
            text(
                "SELECT pg_advisory_xact_lock("
                "hashtextextended(:lock_key, 0))"
            ),
            {"lock_key": lock_key},
        )

    def get(
            self,
            idempotency_key: str,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve an idempotency record by key."""
        statement = (
            select(IdempotencyRecordDB)
            .where(
                IdempotencyRecordDB.idempotency_key == idempotency_key
            )
        )
        record_db = self.db.execute(
            statement
        ).scalar_one_or_none()

        if record_db is None:
            return None

        try:
            response = json.loads(record_db.response_json)
        except (json.JSONDecodeError, TypeError) as exc:
            raise RuntimeError(
                "Stored idempotency response contains invalid JSON."
            ) from exc

        if not isinstance(response, dict):
            raise RuntimeError(
                "Stored idempotency response must be a JSON object."
            )

        return {
            "idempotency_key": record_db.idempotency_key,
            "fingerprint": record_db.fingerprint,
            "response": response,
        }

    def add(
            self,
            idempotency_key: str,
            fingerprint: str,
            response: Dict[str, Any],
    ) -> None:
        """
        Persist an idempotency record without committing the transaction.

        If the key already exists, the existing fingerprint is checked.
        A conflicting fingerprint raises ValueError.

        For a matching fingerprint, the existing record is left unchanged.
        The caller remains responsible for returning the previously stored
        response rather than executing the business operation again.
        """
        if not idempotency_key or not idempotency_key.strip():
            raise ValueError("Idempotency key must not be empty.")

        if not fingerprint or not fingerprint.strip():
            raise ValueError("Request fingerprint must not be empty.")

        if not isinstance(response, dict):
            raise ValueError("Idempotency response must be a dictionary.")

        try:
            response_json = json.dumps(
                response,
                separators=(",", ":"),
                sort_keys=True,
                allow_nan=False,
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Idempotency response must be JSON serializable."
            ) from exc

        statement = (
            insert(IdempotencyRecordDB)
            .values(
                id=str(uuid4()),
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                response_json=response_json,
            )
            .on_conflict_do_nothing(
                index_elements=[
                    IdempotencyRecordDB.idempotency_key,
                ],
            )
        )

        result = self.db.execute(statement)

        if result.rowcount == 1:
            self.db.flush()
            return

        existing_statement = (
            select(IdempotencyRecordDB)
            .where(
                IdempotencyRecordDB.idempotency_key == idempotency_key
            )
            .with_for_update()
        )
        existing_record = self.db.execute(
            existing_statement
        ).scalar_one_or_none()

        if existing_record is None:
            raise RuntimeError(
                "An idempotency conflict occurred, but the existing "
                "record could not be retrieved."
            )

        if existing_record.fingerprint != fingerprint:
            raise ValueError(
                "Idempotency-Key has already been used for a different "
                "request."
            )

        # A matching key and fingerprint must not overwrite the original
        # response. The caller must retrieve and replay that response.
