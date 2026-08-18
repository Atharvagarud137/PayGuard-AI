from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.models import AuditEvent, AuditEventType
from app.repositories.audit_repository import AuditRepository


class AuditService:
    """
    Application service responsible for creating audit events.

    The AuditService centralizes audit-event creation so API routes and
    payment services do not need to know how audit records are persisted.

    Security principle:

        Audit events must contain operational information required for
        traceability without storing sensitive payment credentials,
        authentication secrets, or full card numbers.
    """

    def __init__(
            self,
            repository: AuditRepository,
    ) -> None:
        self.repository = repository

    # -----------------------------------------------------------------------
    # Event Creation
    # -----------------------------------------------------------------------

    def record(
            self,
            event_type: AuditEventType,
            action: str,
            outcome: str,
            correlation_id: Optional[str] = None,
            transaction_id: Optional[str] = None,
            card_id: Optional[str] = None,
            merchant_id: Optional[str] = None,
            amount: Optional[Any] = None,
            detail: Optional[str] = None,
    ) -> AuditEvent:
        """
        Create and persist an audit event.

        Only explicitly supplied operational metadata is recorded.

        The method intentionally does not accept arbitrary request payloads.
        This prevents accidental persistence of sensitive data.
        """

        event = AuditEvent(
            event_type=event_type,
            action=action,
            outcome=outcome,
            correlation_id=correlation_id,
            transaction_id=transaction_id,
            card_id=card_id,
            merchant_id=merchant_id,
            amount=amount,
            detail=detail,
            timestamp=datetime.now(timezone.utc),
        )

        self.repository.add(event)

        return event

    # -----------------------------------------------------------------------
    # Query Operations
    # -----------------------------------------------------------------------

    def get(
            self,
            audit_event_id: str,
    ) -> Optional[AuditEvent]:
        """
        Retrieve an audit event by ID.
        """

        return self.repository.get(audit_event_id)

    def list_all(self):
        """
        Retrieve all audit events.
        """

        return self.repository.list_all()

    def list_by_transaction(
            self,
            transaction_id: str,
    ):
        """
        Retrieve audit events associated with a transaction.
        """

        return self.repository.list_by_transaction(
            transaction_id
        )

    def list_by_correlation_id(
            self,
            correlation_id: str,
    ):
        """
        Retrieve audit events associated with a request correlation ID.
        """

        return self.repository.list_by_correlation_id(
            correlation_id
        )