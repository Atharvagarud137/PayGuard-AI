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

    This repository translates between the domain Card model in
    app.models and the SQLAlchemy CardDB persistence model.

    Business rules remain in the service/domain layers. The repository is
    responsible for persistence, retrieval, and mapping between domain and
    database representations.

    Card retrieval for mutation operations is supported through
    get_for_update(), which acquires a PostgreSQL row-level lock. This is
    required to prevent concurrent authorization operations from reading
    and modifying the same card balance simultaneously.
    """

    def __init__(
            self,
            db: Session,
    ) -> None:
        self.db = db

    # -----------------------------------------------------------------------
    # Card Operations
    # -----------------------------------------------------------------------

    def add(
            self,
            card: Card,
    ) -> None:
        """
        Persist a new card in PostgreSQL.
        """
        card_db = self._to_db_model(card)

        self.db.add(card_db)
        self.db.flush()

    def get(
            self,
            card_id: str,
    ) -> Optional[Card]:
        """
        Retrieve a card by its unique identifier.

        This is a read-only retrieval and does not acquire a database lock.

        Returns:
            The domain Card if found, otherwise None.
        """
        statement = select(CardDB).where(
            CardDB.id == card_id,
            )

        card_db = self.db.execute(statement).scalar_one_or_none()

        if card_db is None:
            return None

        return self._to_domain_model(card_db)

    def get_for_update(
            self,
            card_id: str,
    ) -> Optional[Card]:
        """
        Retrieve a card while acquiring a PostgreSQL row-level lock.

        The lock remains held for the lifetime of the current database
        transaction. Concurrent transactions attempting to acquire a lock
        on the same card must wait until the current transaction commits or
        rolls back.

        This operation is intended for payment lifecycle operations that
        mutate card state, particularly authorization where the available
        balance is read and then modified.

        Returns:
            The domain Card if found, otherwise None.
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

    def update(
            self,
            card: Card,
    ) -> None:
        """
        Persist changes to an existing card.

        Raises:
            ValueError:
                If the card does not exist in PostgreSQL.
        """
        statement = select(CardDB).where(
            CardDB.id == card.card_id,
            )

        card_db = self.db.execute(statement).scalar_one_or_none()

        if card_db is None:
            raise ValueError(
                f"Card '{card.card_id}' does not exist.",
            )

        card_db.card_number = card.card_number
        card_db.cardholder_name = card.cardholder_name
        card_db.network = card.network.value
        card_db.balance = Decimal(card.balance)
        card_db.status = card.status.value
        card_db.expiry_date = card.expiry_date

        self.db.flush()

    def exists_with_number(
            self,
            card_number: str,
    ) -> bool:
        """
        Check whether a card with the supplied card number exists.

        The database also enforces uniqueness on card_number, so this
        method is an application-level existence check rather than the
        final concurrency guarantee.
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

    # -----------------------------------------------------------------------
    # Mapping Helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _to_db_model(
            card: Card,
    ) -> CardDB:
        """
        Convert a domain Card into a SQLAlchemy CardDB instance.
        """
        return CardDB(
            id=card.card_id,
            card_number=card.card_number,
            cardholder_name=card.cardholder_name,
            network=card.network.value,
            balance=Decimal(card.balance),
            status=card.status.value,
            expiry_date=card.expiry_date,
            created_at=card.created_at,
        )

    @staticmethod
    def _to_domain_model(
            card_db: CardDB,
    ) -> Card:
        """
        Convert a SQLAlchemy CardDB instance into the domain Card model.
        """
        return Card(
            card_id=card_db.id,
            card_number=card_db.card_number,
            cardholder_name=card_db.cardholder_name,
            network=card_db.network,
            balance=card_db.balance,
            status=card_db.status,
            expiry_date=card_db.expiry_date,
            created_at=card_db.created_at,
        )