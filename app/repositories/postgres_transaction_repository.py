
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database_models import TransactionDB, TransactionEventDB
from app.models import Transaction, TransactionEvent
from app.repositories.interfaces import TransactionRepositoryProtocol


class PostgresTransactionRepository(TransactionRepositoryProtocol):
    """
    PostgreSQL-backed implementation of the transaction repository.

    Translates between domain models and SQLAlchemy persistence models.
    Transaction lifecycle rules remain in the service/domain layers.

    The repository does not commit or roll back transactions. The caller
    owns transaction boundaries so a payment operation can execute
    atomically within a single database transaction.

    Lifecycle operations that perform read-modify-write transitions should
    use get_for_update() to serialize concurrent updates to the same row.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, transaction: Transaction) -> None:
        """Persist a transaction and its initial lifecycle history."""
        transaction_db = self._to_db_model(transaction)

        self.db.add(transaction_db)
        self.db.flush()

        for event in transaction.history:
            self.db.add(
                self._event_to_db_model(
                    event=event,
                    transaction_id=transaction.transaction_id,
                )
            )

        self.db.flush()

    def get(self, transaction_id: str) -> Optional[Transaction]:
        """Retrieve a transaction without explicitly acquiring a row lock."""
        statement = (
            select(TransactionDB)
            .where(TransactionDB.id == transaction_id)
        )
        transaction_db = self.db.execute(
            statement
        ).scalar_one_or_none()

        if transaction_db is None:
            return None

        return self._to_domain_model(transaction_db)

    def get_for_update(
            self,
            transaction_id: str,
    ) -> Optional[Transaction]:
        """
        Retrieve a transaction while acquiring a PostgreSQL row-level lock.

        The lock remains held until the surrounding transaction commits
        or rolls back.
        """
        statement = (
            select(TransactionDB)
            .where(TransactionDB.id == transaction_id)
            .with_for_update()
        )
        transaction_db = self.db.execute(
            statement
        ).scalar_one_or_none()

        if transaction_db is None:
            return None

        return self._to_domain_model(transaction_db)

    def update(self, transaction: Transaction) -> None:
        """
        Persist changes to an existing transaction and append new events.

        Existing persisted events are preserved. The caller must acquire
        the transaction row lock before read-modify-write lifecycle changes.

        Raises:
            ValueError: If the transaction does not exist.
        """
        statement = (
            select(TransactionDB)
            .where(TransactionDB.id == transaction.transaction_id)
        )
        transaction_db = self.db.execute(
            statement
        ).scalar_one_or_none()

        if transaction_db is None:
            raise ValueError(
                f"Transaction '{transaction.transaction_id}' does not exist."
            )

        transaction_db.card_id = transaction.card_id
        transaction_db.merchant_id = transaction.merchant_id
        transaction_db.authorized_amount = Decimal(
            str(transaction.authorized_amount)
        )
        transaction_db.captured_amount = Decimal(
            str(transaction.captured_amount)
        )
        transaction_db.settled_amount = Decimal(
            str(transaction.settled_amount)
        )
        transaction_db.refunded_amount = Decimal(
            str(transaction.refunded_amount)
        )
        transaction_db.status = transaction.status.value
        transaction_db.decline_reason = transaction.decline_reason

        self._synchronize_events(
            transaction_db=transaction_db,
            transaction=transaction,
        )

        self.db.flush()

    @staticmethod
    def _to_db_model(transaction: Transaction) -> TransactionDB:
        """Convert a domain Transaction into its persistence model."""
        return TransactionDB(
            id=transaction.transaction_id,
            card_id=transaction.card_id,
            merchant_id=transaction.merchant_id,
            authorized_amount=Decimal(str(transaction.authorized_amount)),
            captured_amount=Decimal(str(transaction.captured_amount)),
            settled_amount=Decimal(str(transaction.settled_amount)),
            refunded_amount=Decimal(str(transaction.refunded_amount)),
            status=transaction.status.value,
            decline_reason=transaction.decline_reason,
            version=1,
            created_at=transaction.created_at,
        )

    @staticmethod
    def _to_domain_model(transaction_db: TransactionDB) -> Transaction:
        """Convert a persistence model into its domain representation."""
        events = sorted(
            transaction_db.events,
            key=lambda event: (event.created_at, event.id),
        )

        return Transaction(
            transaction_id=transaction_db.id,
            card_id=transaction_db.card_id,
            merchant_id=transaction_db.merchant_id,
            authorized_amount=transaction_db.authorized_amount,
            captured_amount=transaction_db.captured_amount,
            settled_amount=transaction_db.settled_amount,
            refunded_amount=transaction_db.refunded_amount,
            status=transaction_db.status,
            decline_reason=transaction_db.decline_reason,
            history=[
                PostgresTransactionRepository._event_to_domain_model(event)
                for event in events
            ],
            created_at=transaction_db.created_at,
        )

    @staticmethod
    def _event_to_db_model(
            event: TransactionEvent,
            transaction_id: str,
    ) -> TransactionEventDB:
        """
        Convert a domain event into a persistence event.

        The current domain model represents lifecycle events using status,
        timestamp, and detail. The persistence model stores the status as
        both event_type and status, and stores detail in metadata_json.
        """
        metadata_json = (
            {"detail": event.detail}
            if event.detail is not None
            else None
        )

        return TransactionEventDB(
            id=str(uuid4()),
            transaction_id=transaction_id,
            event_type=event.status.value,
            amount=None,
            status=event.status.value,
            metadata_json=metadata_json,
            created_at=event.timestamp,
        )

    @staticmethod
    def _event_to_domain_model(
            event_db: TransactionEventDB,
    ) -> TransactionEvent:
        """Convert a persisted lifecycle event into the domain model."""
        detail = None

        if event_db.metadata_json:
            detail = event_db.metadata_json.get("detail")

        return TransactionEvent(
            status=event_db.status,
            timestamp=event_db.created_at,
            detail=detail,
        )

    def _synchronize_events(
            self,
            transaction_db: TransactionDB,
            transaction: Transaction,
    ) -> None:
        """
        Append events added to the domain history since the last read.

        This uses the append-only history convention: the persisted history
        must be a prefix of the domain history. It does not modify or delete
        existing database events.
        """
        existing_events = sorted(
            transaction_db.events,
            key=lambda event: (event.created_at, event.id),
        )
        domain_events = transaction.history

        existing_count = len(existing_events)

        if existing_count > len(domain_events):
            raise ValueError(
                "Domain transaction history is shorter than persisted history."
            )

        for index, persisted_event in enumerate(existing_events):
            domain_event = domain_events[index]

            persisted_detail = None
            if persisted_event.metadata_json:
                persisted_detail = persisted_event.metadata_json.get("detail")

            if (
                    persisted_event.status != domain_event.status.value
                    or persisted_event.created_at != domain_event.timestamp
                    or persisted_detail != domain_event.detail
            ):
                raise ValueError(
                    "Domain transaction history does not match persisted history."
                )

        for event in domain_events[existing_count:]:
            self.db.add(
                self._event_to_db_model(
                    event=event,
                    transaction_id=transaction.transaction_id,
                )
            )
