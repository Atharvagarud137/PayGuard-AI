from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, List, Optional

from app.models import AuditEvent, AuditEventType
from app.repositories.interfaces import AuditRepositoryProtocol
from app.security import redact_sensitive_text


class AuditService:
    """
    Application service responsible for creating audit events.

    The AuditService centralizes audit-event creation so API routes and
    payment services do not need to know how audit records are persisted.

    The service depends on AuditRepositoryProtocol rather than a concrete
    persistence implementation, allowing the underlying storage mechanism
    to change without changing audit business logic.

    Security principle:

        Audit events must contain operational information required for
        traceability without storing sensitive payment credentials,
        authentication secrets, or full card numbers.
    """

    def __init__(
            self,
            repository: AuditRepositoryProtocol,
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

        Monetary values are normalized through Decimal before being passed
        to the domain model so audit persistence does not depend on binary
        floating-point representation.
        """
        normalized_amount: Optional[Decimal] = None

        if amount is not None:
            normalized_amount = Decimal(
                str(amount),
            )

        safe_text = lambda value: (
            redact_sensitive_text(value)
            if value is not None
            else None
        )

        event = AuditEvent(
            event_type=event_type,
            action=redact_sensitive_text(action),
            outcome=redact_sensitive_text(outcome),
            correlation_id=safe_text(correlation_id),
            transaction_id=safe_text(transaction_id),
            card_id=safe_text(card_id),
            merchant_id=safe_text(merchant_id),
            amount=normalized_amount,
            detail=safe_text(detail),
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
        return self.repository.get(
            audit_event_id,
        )

    def list_all(self) -> List[AuditEvent]:
        """
        Retrieve all audit events.
        """
        return self.repository.list_all()

    def list_by_transaction(
            self,
            transaction_id: str,
    ) -> List[AuditEvent]:
        """
        Retrieve audit events associated with a transaction.
        """
        return self.repository.list_by_transaction(
            transaction_id,
        )

    def list_by_correlation_id(
            self,
            correlation_id: str,
    ) -> List[AuditEvent]:
        """
        Retrieve audit events associated with a request correlation ID.
        """
        return self.repository.list_by_correlation_id(
            correlation_id,
        )

    def verify_integrity(self) -> dict:
        """Return the repository's persistent audit-chain integrity result."""
        verifier = getattr(self.repository, "verify_integrity", None)
        if verifier is None:
            raise NotImplementedError(
                "The configured audit repository does not support "
                "persistent integrity verification."
            )
        return verifier()
