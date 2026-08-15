from typing import Optional

from app.models import Card
from app.storage import InMemoryStorage, storage


class CardRepository:
    """
    Persistence abstraction for card data.

    The repository isolates card persistence from the API layer and supports
    dependency injection while retaining compatibility with the application's
    shared in-memory storage.

    A database-backed implementation can replace the storage backend later
    without requiring changes to the API or business logic.
    """

    def __init__(
            self,
            storage_backend: Optional[InMemoryStorage] = None,
    ) -> None:
        self.storage = storage_backend or storage

    # -----------------------------------------------------------------------
    # Card Operations
    # -----------------------------------------------------------------------

    def add(
            self,
            card: Card,
    ) -> None:
        """
        Persist a new card.
        """
        self.storage.add_card(card)

    def get(
            self,
            card_id: str,
    ) -> Optional[Card]:
        """
        Retrieve a card by its unique identifier.

        Returns:
            The card if found, otherwise None.
        """
        return self.storage.get_card(card_id)

    def update(
            self,
            card: Card,
    ) -> None:
        """
        Persist changes to an existing card.
        """
        self.storage.update_card(card)

    def exists_with_number(
            self,
            card_number: str,
    ) -> bool:
        """
        Check whether a card with the supplied card number already exists.
        """
        return self.storage.card_exists_with_number(card_number)