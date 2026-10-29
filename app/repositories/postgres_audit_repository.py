
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

    Translates between the domain AuditEvent model and its SQLAlchemy
    persistence representation.

    Additional domain fields are stored in metadata_json when they do not
    have dedicated database columns.

    Audit events are append-only through this repository. The repository
    does not commit or roll back transactions; the caller owns transaction
    boundaries.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, event: AuditEvent) -> None:
        """Persist a new audit event within the caller's transaction."""
        event_db = self._to_db_model(event)
        self.db.add(event_db)
        self.db.flush()

    def get(self, audit_event_id: str) -> Optional[AuditEvent]:
        """Retrieve an audit event by its unique identifier."""
        statement = (
            select(AuditEventDB)
            .where(AuditEventDB.id == audit_event_id)
        )
        event_db = self.db.execute(
            statement
        ).scalar_one_or_none()

        if event_db is None:
            return None

        return self._to_domain_model(event_db)

    def list_all(self) -> List[AuditEvent]:
        """Retrieve all audit events in chronological order."""
        statement = select(AuditEventDB).order_by(
            AuditEventDB.created_at.asc(),
            AuditEventDB.id.asc(),
        )
        events_db = self.db.execute(statement).scalars().all()

        return [
            self._to_domain_model(event_db)
            for event_db in events_db
        ]

    def list_by_transaction(
            self,
            transaction_id: str,
    ) -> List[AuditEvent]:
        """Retrieve audit events associated with a transaction."""
        statement = (
            select(AuditEventDB)
            .where(AuditEventDB.transaction_id == transaction_id)
            .order_by(
                AuditEventDB.created_at.asc(),
                AuditEventDB.id.asc(),
            )
        )
        events_db = self.db.execute(statement).scalars().all()

        return [
            self._to_domain_model(event_db)
            for event_db in events_db
        ]

    def list_by_correlation_id(
            self,
            correlation_id: str,
    ) -> List[AuditEvent]:
        """Retrieve audit events associated with a correlation ID."""
        statement = (
            select(AuditEventDB)
            .where(AuditEventDB.correlation_id == correlation_id)
            .order_by(
                AuditEventDB.created_at.asc(),
                AuditEventDB.id.asc(),
            )
        )
        events_db = self.db.execute(statement).scalars().all()

        return [
            self._to_domain_model(event_db)
            for event_db in events_db
        ]

    @staticmethod
    def _event_type_to_string(event_type: Any) -> str:
        """Convert an enum or string event type into its string value."""
        value = getattr(event_type, "value", event_type)
        return str(value)

    @staticmethod
    def _to_db_model(event: AuditEvent) -> AuditEventDB:
        """
        Convert a domain audit event into its persistence representation.

        Monetary amounts are stored as strings in JSON metadata to preserve
        their decimal representation.
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
                event.event_type
            ),
            message=event.detail or event.action,
            correlation_id=event.correlation_id or "unknown",
            metadata_json=metadata,
            created_at=event.timestamp,
        )

    @staticmethod
    def _to_domain_model(event_db: AuditEventDB) -> AuditEvent:
        """Restore a domain audit event from its persisted representation."""
        metadata = event_db.metadata_json or {}

        amount_value = metadata.get("amount")
        amount = (
            Decimal(str(amount_value))
            if amount_value is not None
            else None
        )

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
            detail=metadata.get("detail", event_db.message),
            timestamp=event_db.created_at,
        )
