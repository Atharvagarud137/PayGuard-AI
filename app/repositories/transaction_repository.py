from typing import Optional

from app.models import Transaction
from app.repositories.interfaces import TransactionRepositoryProtocol
from app.storage import InMemoryStorage, storage


class TransactionRepository(TransactionRepositoryProtocol):
    """
    Concrete persistence implementation for transaction data.

    This implementation uses the in-memory storage backend and is retained
    for unit tests and local development.

    Application services depend on TransactionRepositoryProtocol rather than
    this concrete implementation.

    The PostgreSQL-backed implementation is provided separately by
    PostgresTransactionRepository.
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
        Persist a new transaction in the in-memory backend.
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

    def get_for_update(
            self,
            transaction_id: str,
    ) -> Optional[Transaction]:
        """
        Retrieve a transaction for an update operation.

        The in-memory backend does not provide database row-level locking.
        This method therefore has the same retrieval behavior as get().

        PostgreSQL-backed implementations override this behavior with
        SELECT ... FOR UPDATE.
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