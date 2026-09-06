from typing import Optional

from app.models import Transaction
from app.repositories.interfaces import TransactionRepositoryProtocol
from app.storage import InMemoryStorage, storage


class TransactionRepository(TransactionRepositoryProtocol):
    """
    Concrete persistence implementation for transaction data.

    This implementation currently uses the in-memory storage backend.
    Application services should depend on TransactionRepositoryProtocol
    rather than this concrete class.

    The storage backend is injectable so the repository can later be backed
    by PostgreSQL without changing the service-layer contract.
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