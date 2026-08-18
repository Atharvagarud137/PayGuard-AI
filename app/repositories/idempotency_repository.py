from typing import Any, Dict, Optional

from app.storage import InMemoryStorage, storage


class IdempotencyRepository:
    """
    Persistence abstraction for idempotency records.

    The repository deliberately contains no idempotency business rules.
    It only provides persistence operations.

    This allows the current in-memory implementation to later be replaced
    by a PostgreSQL-backed implementation without changing the API or
    service-level idempotency behavior.
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