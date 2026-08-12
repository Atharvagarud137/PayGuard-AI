from typing import Optional

from app.models import Transaction
from app.storage import storage


class TransactionRepository:
    """Persistence abstraction for transaction data."""

    def add(self, transaction: Transaction) -> None:
        storage.add_transaction(transaction)

    def get(self, transaction_id: str) -> Optional[Transaction]:
        return storage.get_transaction(transaction_id)

    def update(self, transaction: Transaction) -> None:
        storage.update_transaction(transaction)