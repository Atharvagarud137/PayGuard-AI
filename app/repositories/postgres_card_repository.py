
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database_models import CardDB
from app.models import Card
from app.repositories.interfaces import CardRepositoryProtocol


class PostgresCardRepository(CardRepositoryProtocol):
    """
    PostgreSQL-backed implementation of the card repository.

    Translates between the domain Card model and the SQLAlchemy CardDB
    persistence model. Business rules remain in the service and domain
    layers.

    The repository does not commit or roll back transactions. Transaction
    boundaries remain under the control of the caller.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, card: Card) -> None:
        """Persist a new card within the caller's transaction."""
        card_db = self._to_db_model(card)
        self.db.add(card_db)
        self.db.flush()

    def get(self, card_id: str) -> Optional[Card]:
        """Retrieve a card by ID without explicitly acquiring a row lock."""
        statement = select(CardDB).where(CardDB.id == card_id)
        card_db = self.db.execute(statement).scalar_one_or_none()

        if card_db is None:
            return None

        return self._to_domain_model(card_db)

    def get_for_update(self, card_id: str) -> Optional[Card]:
        """
        Retrieve a card while acquiring a PostgreSQL row-level lock.

        The lock is held until the surrounding transaction commits or rolls
        back. Concurrent transactions attempting to lock the same row must
        wait, allowing the service to read and update the balance safely
        within a single transaction.
        """
        statement = (
            select(CardDB)
            .where(CardDB.id == card_id)
            .with_for_update()
        )
        card_db = self.db.execute(statement).scalar_one_or_none()

        if card_db is None:
            return None

        return self._to_domain_model(card_db)

    def update(self, card: Card) -> None:
        """
        Persist changes to an existing card.

        Raises:
            ValueError: If the card does not exist.
        """
        statement = select(CardDB).where(CardDB.id == card.card_id)
        card_db = self.db.execute(statement).scalar_one_or_none()

        if card_db is None:
            raise ValueError(f"Card '{card.card_id}' does not exist.")

        card_db.card_number = card.card_number
        card_db.cardholder_name = card.cardholder_name
        card_db.network = card.network.value
        card_db.balance = Decimal(str(card.balance))
        card_db.status = card.status.value
        card_db.expiry_date = card.expiry_date

        self.db.flush()

    def exists_with_number(self, card_number: str) -> bool:
        """
        Check whether a card number already exists.

        The database uniqueness constraint remains the final safeguard
        against concurrent attempts to insert duplicate card numbers.
        """
        statement = (
            select(CardDB.id)
            .where(CardDB.card_number == card_number)
            .limit(1)
        )

        return (
                self.db.execute(statement).scalar_one_or_none()
                is not None
        )

    @staticmethod
    def _to_db_model(card: Card) -> CardDB:
        """Convert a domain Card into a SQLAlchemy CardDB instance."""
        return CardDB(
            id=card.card_id,
            card_number=card.card_number,
            cardholder_name=card.cardholder_name,
            network=card.network.value,
            balance=Decimal(str(card.balance)),
            status=card.status.value,
            expiry_date=card.expiry_date,
            created_at=card.created_at,
        )

    @staticmethod
    def _to_domain_model(card_db: CardDB) -> Card:
        """Convert a SQLAlchemy CardDB instance into the domain model."""
        return Card(
            card_id=card_db.id,
            cardholder_name=card_db.cardholder_name,
            card_number=card_db.card_number,
            network=card_db.network,
            balance=card_db.balance,
            status=card_db.status,
            expiry_date=card_db.expiry_date,
            created_at=card_db.created_at,
        )
