import json
from typing import Any, Dict, Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database_models import IdempotencyRecordDB
from app.repositories.interfaces import IdempotencyRepositoryProtocol


class PostgresIdempotencyRepository(IdempotencyRepositoryProtocol):
    """
    PostgreSQL-backed implementation of the idempotency repository.

    Idempotency records are persisted independently of the payment domain
    models so previously completed requests can be recognized across
    application instances and process restarts.

    The repository does not commit transactions. Transaction boundaries
    remain under the control of the caller.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, idempotency_key: str) -> Optional[Dict[str, Any]]:
        statement = select(IdempotencyRecordDB).where(
            IdempotencyRecordDB.idempotency_key == idempotency_key
        )
        record_db = self.db.execute(statement).scalar_one_or_none()

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
        record_db = IdempotencyRecordDB(
            id=str(uuid4()),
            idempotency_key=idempotency_key,
            fingerprint=fingerprint,
            response_json=json.dumps(
                response,
                separators=(",", ":"),
                sort_keys=True,
                default=str,
            ),
        )

        self.db.add(record_db)
        self.db.flush()