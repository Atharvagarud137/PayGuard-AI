from typing import Dict, Optional

from app.models import Card, Transaction


class InMemoryStorage:
    """
    In-memory persistence implementation used for local development and tests.

    This class is intentionally limited to persistence operations.

    Business rules such as:
        - authorization
        - capture
        - settlement
        - refunds
        - transaction state validation
        - idempotency

    must remain outside this class.

    The storage implementation is kept simple so it can later be replaced
    by a database-backed persistence layer without requiring changes to the
    service layer.
    """

    def __init__(self) -> None:
        self.cards: Dict[str, Card] = {}
        self.transactions: Dict[str, Transaction] = {}

    # -----------------------------------------------------------------------
    # Card Operations
    # -----------------------------------------------------------------------

    def add_card(self, card: Card) -> None:
        """
        Persist a new card.
        """
        self.cards[card.card_id] = card

    def get_card(
            self,
            card_id: str,
    ) -> Optional[Card]:
        """
        Retrieve a card by its unique identifier.

        Returns:
            The card if found, otherwise None.
        """
        return self.cards.get(card_id)

    def update_card(
            self,
            card: Card,
    ) -> None:
        """
        Persist the current state of an existing card.
        """
        self.cards[card.card_id] = card

    def card_exists_with_number(
            self,
            card_number: str,
    ) -> bool:
        """
        Check whether a card with the supplied card number already exists.

        The mock gateway currently stores masked card numbers, so uniqueness
        is checked against the stored masked value.
        """
        return any(
            existing_card.card_number == card_number
            for existing_card in self.cards.values()
        )

    # -----------------------------------------------------------------------
    # Transaction Operations
    # -----------------------------------------------------------------------

    def add_transaction(
            self,
            transaction: Transaction,
    ) -> None:
        """
        Persist a new transaction.
        """
        self.transactions[transaction.transaction_id] = transaction

    def get_transaction(
            self,
            transaction_id: str,
    ) -> Optional[Transaction]:
        """
        Retrieve a transaction by its unique identifier.

        Returns:
            The transaction if found, otherwise None.
        """
        return self.transactions.get(transaction_id)

    def update_transaction(
            self,
            transaction: Transaction,
    ) -> None:
        """
        Persist the current state of an existing transaction.
        """
        self.transactions[transaction.transaction_id] = transaction

    # -----------------------------------------------------------------------
    # Test / Development Utilities
    # -----------------------------------------------------------------------

    def reset(self) -> None:
        """
        Clear all persisted cards and transactions.

        This method exists for test isolation and local development.

        A production database-backed implementation should not expose an
        equivalent destructive operation through application code.
        """
        self.cards.clear()
        self.transactions.clear()


# ---------------------------------------------------------------------------
# Application Storage
# ---------------------------------------------------------------------------

# Shared in-memory storage instance used by the application.
#
# This remains the default persistence implementation while the project
# uses in-memory storage. Repositories depend on this abstraction rather
# than allowing business services to access storage directly.
storage = InMemoryStorage()