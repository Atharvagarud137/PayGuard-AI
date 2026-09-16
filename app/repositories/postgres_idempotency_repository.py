import json
from typing import Any, Dict, Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.database_models import IdempotencyRecordDB
from app.repositories.interfaces import IdempotencyRepositoryProtocol


class PostgresIdempotencyRepository(IdempotencyRepositoryProtocol):
    """
    PostgreSQL-backed implementation of the idempotency repository.

    Idempotency records are persisted independently of the payment domain
    models so previously completed requests can be recognized across
    application instances and process restarts.

    The repository does not commit or rollback transactions. Transaction
    boundaries remain under the control of the caller.

    PostgreSQL's unique constraint on idempotency_key provides the
    persistence-level uniqueness guarantee. Inserts use ON CONFLICT DO
    NOTHING so concurrent requests using the same key do not result in an
    unhandled duplicate-key exception.

    A matching fingerprint indicates reuse of the same request. A different
    fingerprint indicates an invalid attempt to reuse an idempotency key
    for a different request.

    The repository-level uniqueness guarantee does not by itself prevent
    duplicate business operations. Atomic request claiming and lifecycle
    handling must be enforced by the application/service transaction.
    """

    def __init__(
            self,
            db: Session,
    ) -> None:
        self.db = db

    # -----------------------------------------------------------------------
    # Idempotency Operations
    # -----------------------------------------------------------------------

    def get(
            self,
            idempotency_key: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve an idempotency record by key.

        Returns:
            A dictionary containing the key, request fingerprint, and
            previously stored response when found. Otherwise, None.
        """
        statement = (
            select(IdempotencyRecordDB)
            .where(
                IdempotencyRecordDB.idempotency_key == idempotency_key,
                )
        )

        record_db = self.db.execute(
            statement,
        ).scalar_one_or_none()

        if record_db is None:
            return None

        return {
            "idempotency_key": record_db.idempotency_key,
            "fingerprint": record_db.fingerprint,
            "response": json.loads(record_db.response_json),
        }

    def add(
            self,
            idempotency_key: str,
            fingerprint: str,
            response: Dict[str, Any],
    ) -> None:
        """
        Persist a completed idempotent operation.

        The insert is protected by the database-level unique constraint on
        idempotency_key.

        When another concurrent transaction has already inserted the same
        key, ON CONFLICT DO NOTHING prevents a duplicate-key exception.

        The existing record is then inspected:

        - Same fingerprint: the request represents the same operation.
        - Different fingerprint: the key is being reused for a different
          request and is rejected.

        The repository does not commit the transaction.
        """
        response_json = json.dumps(
            response,
            separators=(",", ":"),
            sort_keys=True,
            default=str,
        )

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
                IdempotencyRecordDB.idempotency_key == idempotency_key,
                )
        )

        existing_record = (
            self.db.execute(existing_statement)
            .scalar_one_or_none()
        )

        if existing_record is None:
            raise RuntimeError(
                "Idempotency record conflict occurred, but the existing "
                "record could not be retrieved.",
            )

        if existing_record.fingerprint != fingerprint:
            raise ValueError(
                "Idempotency-Key has already been used for a different "
                "request.",
            )

        self.db.flush()