from typing import Optional

from app.models import Transaction
from app.storage import InMemoryStorage, storage


class TransactionRepository:
    """
    Persistence abstraction for transaction data.

    The repository supports dependency injection while retaining backward
    compatibility with existing callers and unit tests.

    If no storage backend is supplied, the application's shared in-memory
    storage is used. A different storage implementation can be injected
    later without changing the PaymentService interface.
    """

    def __init__(
            self,
            storage_backend: Optional[InMemoryStorage] = None,
    ) -> None:
        self.storage = storage_backend or storage

    # -----------------------------------------------------------------------
    # Transaction Operations
    # -----------------------------------------------------------------------

    def add(self, transaction: Transaction) -> None:
        """
        Persist a new transaction.
        """
        self.storage.add_transaction(transaction)

    def get(
            self,
            transaction_id: str,
    ) -> Optional[Transaction]:
        """
        Retrieve a transaction by its unique identifier.

        Returns:
            Transaction if found, otherwise None.
        """
        return self.storage.get_transaction(transaction_id)

    def update(
            self,
            transaction: Transaction,
    ) -> None:
        """
        Persist changes to an existing transaction.
        """
        self.storage.update_transaction(transaction)