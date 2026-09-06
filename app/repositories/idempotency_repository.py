from typing import Any, Dict, Optional

from app.repositories.interfaces import IdempotencyRepositoryProtocol
from app.storage import InMemoryStorage, storage


class IdempotencyRepository(IdempotencyRepositoryProtocol):
    """
    Concrete persistence implementation for idempotency records.

    The repository deliberately contains no idempotency business rules.
    It only provides persistence operations.

    This implementation currently uses the in-memory storage backend.
    A PostgreSQL-backed implementation can replace it later without
    changing the API or service-level idempotency behavior.
    """

    def __init__(
            self,
            storage_backend: Optional[InMemoryStorage] = None,
    ) -> None:
        self.storage = storage_backend or storage

    def get(
            self,
            idempotency_key: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve an idempotency record by key.
        """
        return self.storage.get_idempotency_record(
            idempotency_key
        )

    def add(
            self,
            idempotency_key: str,
            fingerprint: str,
            response: Dict[str, Any],
    ) -> None:
        """
        Persist a new idempotency record.
        """
        self.storage.add_idempotency_record(
            idempotency_key=idempotency_key,
            fingerprint=fingerprint,
            response=response,
        )