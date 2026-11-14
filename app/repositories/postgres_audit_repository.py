from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.audit_integrity import ZERO_HASH, calculate_audit_hash
from app.database_models import AuditEventDB
from app.models import AuditEvent
from app.repositories.interfaces import AuditRepositoryProtocol


class PostgresAuditRepository(AuditRepositoryProtocol):
    """
    PostgreSQL-backed audit repository.

    Inserts are serialized into a tamper-evident hash chain. Normal updates
    and deletes are rejected by a database trigger installed by Alembic.
    The repository never commits or rolls back; the caller owns the
    transaction boundary.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, event: AuditEvent) -> None:
        """Append an audit event to the globally ordered hash chain."""
        # Flush payment rows first so an audit row referencing a newly created
        # transaction cannot reach PostgreSQL before its foreign-key parent.
        # The flush remains inside the caller's transaction and is rolled back
        # with the payment operation if any later write fails.
        self.db.flush()
        self.db.execute(
            text(
                "SELECT pg_advisory_xact_lock("
                "hashtextextended('payguard-ai:audit-chain', 0))"
            )
        )

        latest = self.db.execute(
            select(AuditEventDB)
            .order_by(AuditEventDB.chain_sequence.desc())
            .limit(1)
        ).scalar_one_or_none()

        sequence = latest.chain_sequence + 1 if latest else 1
        previous_hash = latest.event_hash if latest else ZERO_HASH
        event_db = self._to_db_model(event)
        event_db.chain_sequence = sequence
        event_db.previous_hash = previous_hash
        event_db.event_hash = calculate_audit_hash(
            sequence=sequence,
            previous_hash=previous_hash,
            event_id=event_db.id,
            transaction_id=event_db.transaction_id,
            event_type=event_db.event_type,
            message=event_db.message,
            correlation_id=event_db.correlation_id,
            metadata_json=event_db.metadata_json,
            created_at=event_db.created_at,
        )
        self.db.add(event_db)
        self.db.flush()

    def get(self, audit_event_id: str) -> Optional[AuditEvent]:
        """Retrieve an audit event by its unique identifier."""
        statement = select(AuditEventDB).where(
            AuditEventDB.id == audit_event_id
        )
        event_db = self.db.execute(statement).scalar_one_or_none()
        return (
            self._to_domain_model(event_db)
            if event_db is not None
            else None
        )

    def list_all(self) -> List[AuditEvent]:
        """Retrieve audit events in append order."""
        statement = select(AuditEventDB).order_by(
            AuditEventDB.chain_sequence.asc()
        )
        events_db = self.db.execute(statement).scalars().all()
        return [self._to_domain_model(record) for record in events_db]

    def list_by_transaction(
            self,
            transaction_id: str,
    ) -> List[AuditEvent]:
        """Retrieve audit events for a transaction in append order."""
        statement = (
            select(AuditEventDB)
            .where(AuditEventDB.transaction_id == transaction_id)
            .order_by(AuditEventDB.chain_sequence.asc())
        )
        records = self.db.execute(statement).scalars().all()
        return [self._to_domain_model(record) for record in records]

    def list_by_correlation_id(
            self,
            correlation_id: str,
    ) -> List[AuditEvent]:
        """Retrieve audit events for a correlation ID in append order."""
        statement = (
            select(AuditEventDB)
            .where(AuditEventDB.correlation_id == correlation_id)
            .order_by(AuditEventDB.chain_sequence.asc())
        )
        records = self.db.execute(statement).scalars().all()
        return [self._to_domain_model(record) for record in records]

    def verify_integrity(self) -> dict[str, Any]:
        """Check sequence continuity, previous hashes, and event hashes."""
        records = self.db.execute(
            select(AuditEventDB).order_by(
                AuditEventDB.chain_sequence.asc()
            )
        ).scalars().all()

        previous_hash = ZERO_HASH
        expected_sequence = 1

        for record in records:
            expected_hash = calculate_audit_hash(
                sequence=record.chain_sequence,
                previous_hash=previous_hash,
                event_id=record.id,
                transaction_id=record.transaction_id,
                event_type=record.event_type,
                message=record.message,
                correlation_id=record.correlation_id,
                metadata_json=record.metadata_json,
                created_at=record.created_at,
            )
            if (
                record.chain_sequence != expected_sequence
                or record.previous_hash != previous_hash
                or record.event_hash != expected_hash
            ):
                return {
                    "valid": False,
                    "event_count": len(records),
                    "first_invalid_sequence": record.chain_sequence,
                }

            previous_hash = record.event_hash
            expected_sequence += 1

        return {
            "valid": True,
            "event_count": len(records),
            "first_invalid_sequence": None,
        }

    @staticmethod
    def _event_type_to_string(event_type: Any) -> str:
        """Convert an enum or string event type into its string value."""
        return str(getattr(event_type, "value", event_type))

    @staticmethod
    def _to_db_model(event: AuditEvent) -> AuditEventDB:
        """Convert a domain event into its database representation."""
        metadata: Dict[str, Any] = {
            "action": event.action,
            "outcome": event.outcome,
            "card_id": event.card_id,
            "merchant_id": event.merchant_id,
            "amount": str(event.amount) if event.amount is not None else None,
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
        """Restore a domain event from its database representation."""
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
