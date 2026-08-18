from decimal import Decimal

from app.models import AuditEventType
from app.repositories.audit_repository import AuditRepository
from app.services.audit_service import AuditService
from app.storage import InMemoryStorage


def create_audit_service():
    """
    Create an isolated AuditService instance for unit tests.
    """

    test_storage = InMemoryStorage()

    repository = AuditRepository(
        test_storage
    )

    service = AuditService(
        repository
    )

    return service


def test_record_creates_audit_event():
    """
    Positive case: recording an event should create and persist an
    audit record.
    """

    service = create_audit_service()

    event = service.record(
        event_type=AuditEventType.AUTHORIZATION,
        action="AUTHORIZE",
        outcome="SUCCESS",
        correlation_id="request-001",
        transaction_id="transaction-001",
        card_id="card-001",
        merchant_id="merchant-001",
        amount=Decimal("100.00"),
        detail="Authorization approved",
    )

    assert event.event_type == AuditEventType.AUTHORIZATION
    assert event.action == "AUTHORIZE"
    assert event.outcome == "SUCCESS"
    assert event.correlation_id == "request-001"
    assert event.transaction_id == "transaction-001"
    assert event.card_id == "card-001"
    assert event.merchant_id == "merchant-001"
    assert event.amount == Decimal("100.00")
    assert event.detail == "Authorization approved"
    assert event.audit_event_id


def test_record_persists_event():
    """
    The created audit event should be retrievable from the repository.
    """

    service = create_audit_service()

    event = service.record(
        event_type=AuditEventType.CAPTURE,
        action="CAPTURE",
        outcome="SUCCESS",
        transaction_id="transaction-002",
    )

    stored_event = service.get(
        event.audit_event_id
    )

    assert stored_event is not None
    assert stored_event.audit_event_id == event.audit_event_id
    assert stored_event.event_type == AuditEventType.CAPTURE
    assert stored_event.action == "CAPTURE"
    assert stored_event.outcome == "SUCCESS"


def test_audit_event_has_timestamp():
    """
    Every audit event should receive a UTC timestamp.
    """

    service = create_audit_service()

    event = service.record(
        event_type=AuditEventType.SETTLEMENT,
        action="SETTLE",
        outcome="SUCCESS",
    )

    assert event.timestamp is not None
    assert event.timestamp.tzinfo is not None


def test_list_by_transaction():
    """
    Transaction-specific audit queries should return only matching events.
    """

    service = create_audit_service()

    service.record(
        event_type=AuditEventType.AUTHORIZATION,
        action="AUTHORIZE",
        outcome="SUCCESS",
        transaction_id="transaction-001",
    )

    service.record(
        event_type=AuditEventType.CAPTURE,
        action="CAPTURE",
        outcome="SUCCESS",
        transaction_id="transaction-001",
    )

    service.record(
        event_type=AuditEventType.AUTHORIZATION,
        action="AUTHORIZE",
        outcome="SUCCESS",
        transaction_id="transaction-002",
    )

    events = service.list_by_transaction(
        "transaction-001"
    )

    assert len(events) == 2

    assert all(
        event.transaction_id == "transaction-001"
        for event in events
    )


def test_list_by_correlation_id():
    """
    Correlation-ID queries should return only events associated with
    the specified request.
    """

    service = create_audit_service()

    service.record(
        event_type=AuditEventType.AUTHORIZATION,
        action="AUTHORIZE",
        outcome="SUCCESS",
        correlation_id="request-001",
    )

    service.record(
        event_type=AuditEventType.CAPTURE,
        action="CAPTURE",
        outcome="SUCCESS",
        correlation_id="request-001",
    )

    service.record(
        event_type=AuditEventType.REFUND,
        action="REFUND",
        outcome="SUCCESS",
        correlation_id="request-002",
    )

    events = service.list_by_correlation_id(
        "request-001"
    )

    assert len(events) == 2

    assert all(
        event.correlation_id == "request-001"
        for event in events
    )


def test_audit_event_supports_failed_operations():
    """
    Audit events should represent both successful and failed operations.
    """

    service = create_audit_service()

    event = service.record(
        event_type=AuditEventType.SECURITY,
        action="AUTHORIZE",
        outcome="FAILURE",
        correlation_id="request-003",
        detail="Card is not active",
    )

    assert event.event_type == AuditEventType.SECURITY
    assert event.outcome == "FAILURE"
    assert event.detail == "Card is not active"


def test_audit_event_does_not_require_sensitive_payload():
    """
    Audit records should be constructible without accepting or requiring
    raw request payloads.

    This test intentionally verifies that operational metadata is sufficient.
    """

    service = create_audit_service()

    event = service.record(
        event_type=AuditEventType.SECURITY,
        action="VALIDATION",
        outcome="FAILURE",
        detail="Request rejected",
    )

    assert event.audit_event_id
    assert event.detail == "Request rejected"