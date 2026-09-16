from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database_models import TransactionDB, TransactionEventDB
from app.models import Transaction, TransactionEvent
from app.repositories.interfaces import TransactionRepositoryProtocol


class PostgresTransactionRepository(TransactionRepositoryProtocol):
    """
    PostgreSQL-backed implementation of the transaction repository.

    This repository translates between the domain models in app.models and
    the SQLAlchemy persistence models in app.database_models.

    Transaction lifecycle rules remain in the service/domain layer.
    This repository is responsible for persistence, retrieval, and mapping.

    The repository does not commit or rollback transactions. Transaction
    boundaries are owned by the caller so that a complete payment operation
    can execute atomically within a single database transaction.

    Lifecycle operations that perform read-modify-write transitions should
    use get_for_update() so PostgreSQL can serialize concurrent updates to
    the same transaction row.
    """

    def __init__(
            self,
            db: Session,
    ) -> None:
        self.db = db

    # -----------------------------------------------------------------------
    # Transaction Operations
    # -----------------------------------------------------------------------

    def add(
            self,
            transaction: Transaction,
    ) -> None:
        """
        Persist a new transaction and its lifecycle history.

        The transaction and all supplied lifecycle events are added to the
        current SQLAlchemy session. The caller owns the eventual commit.
        """
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

    def get(
            self,
            transaction_id: str,
    ) -> Optional[Transaction]:
        """
        Retrieve a transaction by its unique identifier.

        This operation does not acquire a row-level lock.

        Returns:
            The domain Transaction if found, otherwise None.
        """
        statement = (
            select(TransactionDB)
            .where(
                TransactionDB.id == transaction_id,
                )
        )

        transaction_db = (
            self.db.execute(statement)
            .scalar_one_or_none()
        )

        if transaction_db is None:
            return None

        return self._to_domain_model(transaction_db)

    def update(
            self,
            transaction: Transaction,
    ) -> None:
        """
        Persist changes to an existing transaction.

        Transaction lifecycle events are append-only. Existing persisted
        events are preserved, while new events present in the domain
        transaction history are appended.

        The transaction version is not modified here. Concurrency control
        for lifecycle operations is provided by get_for_update() and the
        surrounding database transaction.

        Raises:
            ValueError:
                If the transaction does not exist in PostgreSQL.
        """
        statement = (
            select(TransactionDB)
            .where(
                TransactionDB.id == transaction.transaction_id,
                )
        )

        transaction_db = (
            self.db.execute(statement)
            .scalar_one_or_none()
        )

        if transaction_db is None:
            raise ValueError(
                f"Transaction '{transaction.transaction_id}' does not exist.",
            )

        transaction_db.card_id = transaction.card_id
        transaction_db.merchant_id = transaction.merchant_id

        transaction_db.authorized_amount = Decimal(
            str(transaction.authorized_amount),
        )
        transaction_db.captured_amount = Decimal(
            str(transaction.captured_amount),
        )
        transaction_db.settled_amount = Decimal(
            str(transaction.settled_amount),
        )
        transaction_db.refunded_amount = Decimal(
            str(transaction.refunded_amount),
        )

        transaction_db.status = transaction.status.value
        transaction_db.decline_reason = transaction.decline_reason

        self._synchronize_events(
            transaction_db=transaction_db,
            transaction=transaction,
        )

        self.db.flush()

    # -----------------------------------------------------------------------
    # Concurrency Support
    # -----------------------------------------------------------------------

    def get_for_update(
            self,
            transaction_id: str,
    ) -> Optional[Transaction]:
        """
        Retrieve a transaction while acquiring a PostgreSQL row-level lock.

        The lock remains held until the surrounding database transaction is
        committed or rolled back.

        This method is intended for payment lifecycle operations that perform
        a read-modify-write transition, such as:

            capture
            settlement
            refund

        Concurrent operations attempting to lock the same transaction row
        must wait until the current transaction releases the lock.

        Returns:
            The domain Transaction if found, otherwise None.
        """
        statement = (
            select(TransactionDB)
            .where(
                TransactionDB.id == transaction_id,
                )
            .with_for_update()
        )

        transaction_db = (
            self.db.execute(statement)
            .scalar_one_or_none()
        )

        if transaction_db is None:
            return None

        return self._to_domain_model(transaction_db)

    # -----------------------------------------------------------------------
    # Mapping Helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _to_db_model(
            transaction: Transaction,
    ) -> TransactionDB:
        """
        Convert a domain Transaction into a SQLAlchemy TransactionDB
        instance.
        """
        return TransactionDB(
            id=transaction.transaction_id,
            card_id=transaction.card_id,
            merchant_id=transaction.merchant_id,
            authorized_amount=Decimal(
                str(transaction.authorized_amount),
            ),
            captured_amount=Decimal(
                str(transaction.captured_amount),
            ),
            settled_amount=Decimal(
                str(transaction.settled_amount),
            ),
            refunded_amount=Decimal(
                str(transaction.refunded_amount),
            ),
            status=transaction.status.value,
            decline_reason=transaction.decline_reason,
            version=1,
            created_at=transaction.created_at,
        )

    @staticmethod
    def _to_domain_model(
            transaction_db: TransactionDB,
    ) -> Transaction:
        """
        Convert a SQLAlchemy TransactionDB instance into the domain
        Transaction model.
        """
        events = sorted(
            transaction_db.events,
            key=lambda event: event.created_at,
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
                PostgresTransactionRepository._event_to_domain_model(
                    event,
                )
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
        Convert a domain TransactionEvent into a SQLAlchemy
        TransactionEventDB instance.

        The domain model intentionally contains only status, timestamp,
        and detail. Persistence-specific identifiers and relationships are
        generated here rather than leaking into the domain model.

        The lifecycle status is stored as both event_type and status because
        the current domain event model does not define a separate event
        type.

        The optional domain detail is preserved in metadata_json.
        """
        metadata_json = None

        if event.detail is not None:
            metadata_json = {
                "detail": event.detail,
            }

        return TransactionEventDB(
            id=_generate_event_id(),
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
        """
        Convert a SQLAlchemy TransactionEventDB instance into the domain
        TransactionEvent model.
        """
        detail = None

        if event_db.metadata_json:
            detail = event_db.metadata_json.get("detail")

        return TransactionEvent(
            status=event_db.status,
            timestamp=event_db.created_at,
            detail=detail,
        )

    # -----------------------------------------------------------------------
    # Event Synchronization
    # -----------------------------------------------------------------------

    def _synchronize_events(
            self,
            transaction_db: TransactionDB,
            transaction: Transaction,
    ) -> None:
        """
        Append lifecycle events that exist in the domain history but have
        not yet been persisted.

        TransactionEvent does not contain a persistent identifier, so
        synchronization is based on the append-only history model rather
        than an event ID.

        Existing database events are never modified or deleted.
        """
        existing_events = sorted(
            transaction_db.events,
            key=lambda event: event.created_at,
        )

        existing_count = len(existing_events)
        domain_events = transaction.history

        if existing_count >= len(domain_events):
            return

        new_events = domain_events[existing_count:]

        for event in new_events:
            self.db.add(
                self._event_to_db_model(
                    event=event,
                    transaction_id=transaction.transaction_id,
                )
            )


def _generate_event_id() -> str:
    """
    Generate a persistence-only identifier for a transaction event.

    TransactionEvent intentionally does not expose this identifier in the
    domain model.
    """
    from uuid import uuid4

    return str(uuid4())