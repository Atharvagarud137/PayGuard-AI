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

    The repository does not commit transactions. Transaction boundaries are
    owned by the caller so that a complete payment operation can execute
    atomically within a single database transaction.

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
        Persist a new transaction and its lifecycle events.

        The transaction itself and all supplied events are added to the
        current SQLAlchemy session. The caller owns the eventual commit.
        """
        transaction_db = self._to_db_model(transaction)

        self.db.add(transaction_db)

        for event in transaction.history:
            self.db.add(
                self._event_to_db_model(
                    event,
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

        Existing lifecycle events are treated as append-only records.
        Events already persisted are left unchanged, while newly introduced
        domain events are inserted.

        The persisted transaction version is preserved here. Concurrency
        control is handled by the surrounding transaction and, for lifecycle
        operations, get_for_update().

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
            transaction.authorized_amount
        )

        transaction_db.captured_amount = Decimal(
            transaction.captured_amount
        )

        transaction_db.settled_amount = Decimal(
            transaction.settled_amount
        )

        transaction_db.refunded_amount = Decimal(
            transaction.refunded_amount
        )

        transaction_db.status = transaction.status.value
        transaction_db.decline_reason = transaction.decline_reason

        self._synchronize_events(
            transaction_db,
            transaction,
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
                transaction.authorized_amount
            ),
            captured_amount=Decimal(
                transaction.captured_amount
            ),
            settled_amount=Decimal(
                transaction.settled_amount
            ),
            refunded_amount=Decimal(
                transaction.refunded_amount
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
                    event
                )
                for event in transaction_db.events
            ],
            created_at=transaction_db.created_at,
        )

    @staticmethod
    def _event_to_db_model(
            event: TransactionEvent,
    ) -> TransactionEventDB:
        """
        Convert a domain TransactionEvent into a SQLAlchemy
        TransactionEventDB instance.
        """
        return TransactionEventDB(
            id=event.id,
            transaction_id=event.transaction_id,
            event_type=event.event_type.value,
            amount=(
                Decimal(event.amount)
                if event.amount is not None
                else None
            ),
            status=(
                event.status.value
                if event.status is not None
                else None
            ),
            metadata_json=event.metadata_json,
            created_at=event.created_at,
        )

    @staticmethod
    def _event_to_domain_model(
            event_db: TransactionEventDB,
    ) -> TransactionEvent:
        """
        Convert a SQLAlchemy TransactionEventDB instance into the domain
        TransactionEvent model.
        """
        return TransactionEvent(
            id=event_db.id,
            transaction_id=event_db.transaction_id,
            event_type=event_db.event_type,
            amount=event_db.amount,
            status=event_db.status,
            metadata_json=event_db.metadata_json,
            created_at=event_db.created_at,
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
        Add lifecycle events that exist in the domain transaction but have
        not yet been persisted.

        Transaction events are append-only. Existing events are never
        modified or deleted.
        """
        existing_event_ids = {
            event.id
            for event in transaction_db.events
        }

        for event in transaction.history:
            if event.id in existing_event_ids:
                continue

            self.db.add(
                self._event_to_db_model(
                    event,
                )
            )