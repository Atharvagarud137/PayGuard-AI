from typing import Dict, Optional
from app.models import Card, Transaction


class InMemoryStorage:
    def __init__(self):
        self.cards: Dict[str, Card] = {}
        self.transactions: Dict[str, Transaction] = {}

    # ---------- Card Operations ----------

    def add_card(self, card: Card) -> None:
        self.cards[card.card_id] = card

    def get_card(self, card_id: str) -> Optional[Card]:
        return self.cards.get(card_id)

    def update_card(self, card: Card) -> None:
        self.cards[card.card_id] = card

    def card_exists_with_number(self, card_number: str) -> bool:
        return any(c.card_number == card_number for c in self.cards.values())

    # ---------- Transaction Operations ----------

    def add_transaction(self, transaction: Transaction) -> None:
        self.transactions[transaction.transaction_id] = transaction

    def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        return self.transactions.get(transaction_id)

    def update_transaction(self, transaction: Transaction) -> None:
        self.transactions[transaction.transaction_id] = transaction

    def reset(self) -> None:
        """Clears all data. Useful for test isolation between test runs."""
        self.cards.clear()
        self.transactions.clear()


# Single shared instance used across the entire application
storage = InMemoryStorage()