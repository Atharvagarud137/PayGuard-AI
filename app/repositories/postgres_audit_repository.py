from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database_models import AuditEventDB
from app.models import AuditEvent
from app.repositories.interfaces import AuditRepositoryProtocol


class PostgresAuditRepository(AuditRepositoryProtocol):
    """
    PostgreSQL-backed implementation of the audit repository.

    The domain AuditEvent model remains independent from the SQLAlchemy
    persistence model. This repository is responsible for translating
    between the two representations.

    Audit records are append-only. Existing audit events are never updated
    or deleted through this repository.

    The repository does not commit or rollback transactions. Transaction
    boundaries remain under the control of the caller.
    """

    def __init__(
            self,
            db: Session,
    ) -> None:
        self.db = db

    # -----------------------------------------------------------------------
    # Audit Operations
    # -----------------------------------------------------------------------

    def add(
            self,
            event: AuditEvent,
    ) -> None:
        """
        Persist a new audit event.

        The current PostgreSQL schema stores richer domain attributes such
        as action, outcome, card_id, merchant_id, amount, and detail inside
        metadata_json while retaining the core audit fields as first-class
        database columns.

        The caller owns the surrounding transaction and eventual commit.
        """
        event_db = self._to_db_model(event)

        self.db.add(event_db)
        self.db.flush()

    def get(
            self,
            audit_event_id: str,
    ) -> Optional[AuditEvent]:
        """
        Retrieve an audit event by its unique identifier.

        Returns:
            The domain AuditEvent if found, otherwise None.
        """
        statement = (
            select(AuditEventDB)
            .where(
                AuditEventDB.id == audit_event_id,
                )
        )

        event_db = self.db.execute(
            statement,
        ).scalar_one_or_none()

        if event_db is None:
            return None

        return self._to_domain_model(event_db)

    def list_all(self) -> List[AuditEvent]:
        """
        Retrieve all audit events ordered chronologically.
        """
        statement = (
            select(AuditEventDB)
            .order_by(
                AuditEventDB.created_at.asc(),
                AuditEventDB.id.asc(),
            )
        )

        events_db = (
            self.db.execute(statement)
            .scalars()
            .all()
        )

        return [
            self._to_domain_model(event_db)
            for event_db in events_db
        ]

    def list_by_transaction(
            self,
            transaction_id: str,
    ) -> List[AuditEvent]:
        """
        Retrieve all audit events associated with a transaction.

        Results are returned in chronological order.
        """
        statement = (
            select(AuditEventDB)
            .where(
                AuditEventDB.transaction_id == transaction_id,
                )
            .order_by(
                AuditEventDB.created_at.asc(),
                AuditEventDB.id.asc(),
            )
        )

        events_db = (
            self.db.execute(statement)
            .scalars()
            .all()
        )

        return [
            self._to_domain_model(event_db)
            for event_db in events_db
        ]

    def list_by_correlation_id(
            self,
            correlation_id: str,
    ) -> List[AuditEvent]:
        """
        Retrieve all audit events associated with a correlation ID.

        Results are returned in chronological order.
        """
        statement = (
            select(AuditEventDB)
            .where(
                AuditEventDB.correlation_id == correlation_id,
                )
            .order_by(
                AuditEventDB.created_at.asc(),
                AuditEventDB.id.asc(),
            )
        )

        events_db = (
            self.db.execute(statement)
            .scalars()
            .all()
        )

        return [
            self._to_domain_model(event_db)
            for event_db in events_db
        ]

    # -----------------------------------------------------------------------
    # Mapping Helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _event_type_to_string(
            event_type: Any,
    ) -> str:
        """
        Convert an enum-backed or string event type into its persisted
        string representation.
        """
        value = getattr(
            event_type,
            "value",
            event_type,
        )

        return str(value)

    @staticmethod
    def _to_db_model(
            event: AuditEvent,
    ) -> AuditEventDB:
        """
        Convert a domain AuditEvent into the SQLAlchemy persistence model.

        The domain model contains richer audit information than the current
        database table exposes as first-class columns. Those additional
        fields are persisted in metadata_json.
        """
        metadata: Dict[str, Any] = {
            "action": event.action,
            "outcome": event.outcome,
            "card_id": event.card_id,
            "merchant_id": event.merchant_id,
            "amount": (
                str(event.amount)
                if event.amount is not None
                else None
            ),
            "detail": event.detail,
        }

        return AuditEventDB(
            id=event.audit_event_id,
            transaction_id=event.transaction_id,
            event_type=PostgresAuditRepository._event_type_to_string(
                event.event_type,
            ),
            message=event.detail,
            correlation_id=event.correlation_id,
            metadata_json=metadata,
            created_at=event.timestamp,
        )

    @staticmethod
    def _to_domain_model(
            event_db: AuditEventDB,
    ) -> AuditEvent:
        """
        Convert a SQLAlchemy AuditEventDB instance into the domain
        AuditEvent model.

        Fields stored in metadata_json are restored to their corresponding
        domain attributes.
        """
        metadata = event_db.metadata_json or {}

        amount = metadata.get("amount")

        if amount is not None:
            amount = Decimal(str(amount))

        return AuditEvent(
            audit_event_id=event_db.id,
            event_type=event_db.event_type,
            action=metadata.get("action", ""),
            outcome=metadata.get("outcome", ""),
            correlation_id=event_db.correlation_id,
            transaction_id=event_db.transaction_id,
            card_id=metadata.get("card_id"),
            merchant_id=metadata.get("merchant_id"),
            amount=amount,
            detail=metadata.get(
                "detail",
                event_db.message,
            ),
            timestamp=event_db.created_at,
        )