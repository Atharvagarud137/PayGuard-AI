from typing import Optional

from app.models import Card
from app.repositories.interfaces import CardRepositoryProtocol
from app.storage import InMemoryStorage, storage


class CardRepository(CardRepositoryProtocol):
    """
    Concrete persistence implementation for card data.

    This implementation currently uses the in-memory storage backend.
    Application code should depend on CardRepositoryProtocol rather than
    this concrete implementation.

    The storage backend is injectable so a database-backed implementation
    can be introduced later without changing the repository contract.

    PostgreSQL-backed card persistence is provided separately by
    PostgresCardRepository.

    The get_for_update() method exists for protocol compatibility with
    PostgreSQL-backed repositories. The in-memory backend does not provide
    database row-level locking, so it returns the same result as get().
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

        This is a read-only retrieval and does not acquire a lock.

        Returns:
            The card if found, otherwise None.
        """
        return self.storage.get_card(card_id)

    def get_for_update(
            self,
            card_id: str,
    ) -> Optional[Card]:
        """
        Retrieve a card for a mutation operation.

        The in-memory backend does not support database row-level locking.
        Therefore, this method has the same retrieval behavior as get().

        PostgreSQL-backed implementations override this behavior with
        SELECT ... FOR UPDATE.
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