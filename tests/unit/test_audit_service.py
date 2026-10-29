from datetime import timezone
from decimal import Decimal
from uuid import UUID

import pytest

from app.models import AuditEventType
from app.services.audit_service import AuditService


class FakeAuditRepository:
    """In-memory repository test double for AuditService unit tests."""

    def __init__(self):
        self.events = {}

    def add(self, event):
        self.events[event.audit_event_id] = event
        return event

    def get(self, audit_event_id):
        return self.events.get(audit_event_id)

    def list_all(self):
        return list(self.events.values())

    def list_by_transaction(self, transaction_id):
        return [
            event
            for event in self.events.values()
            if event.transaction_id == transaction_id
        ]

    def list_by_correlation_id(self, correlation_id):
        return [
            event
            for event in self.events.values()
            if event.correlation_id == correlation_id
        ]


@pytest.fixture
def audit_repository():
    return FakeAuditRepository()


@pytest.fixture
def service(audit_repository):
    return AuditService(audit_repository)


def test_record_creates_audit_event(service):
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
    assert event.audit_event_id is not None


def test_record_persists_event(service):
    event = service.record(
        event_type=AuditEventType.CAPTURE,
        action="CAPTURE",
        outcome="SUCCESS",
        correlation_id="request-002",
        transaction_id="transaction-002",
    )

    stored_event = service.get(event.audit_event_id)

    assert stored_event is not None
    assert stored_event.audit_event_id == event.audit_event_id
    assert stored_event.event_type == AuditEventType.CAPTURE
    assert stored_event.action == "CAPTURE"
    assert stored_event.outcome == "SUCCESS"


def test_audit_event_has_timezone_aware_timestamp(service):
    event = service.record(
        event_type=AuditEventType.SETTLEMENT,
        action="SETTLE",
        outcome="SUCCESS",
        correlation_id="request-003",
    )

    assert event.timestamp is not None
    assert event.timestamp.tzinfo is not None
    assert event.timestamp.utcoffset() is not None
    assert event.timestamp.utcoffset().total_seconds() == 0


def test_list_by_transaction_returns_only_matching_events(service):
    service.record(
        event_type=AuditEventType.AUTHORIZATION,
        action="AUTHORIZE",
        outcome="SUCCESS",
        transaction_id="transaction-001",
        correlation_id="request-001",
    )
    service.record(
        event_type=AuditEventType.CAPTURE,
        action="CAPTURE",
        outcome="SUCCESS",
        transaction_id="transaction-001",
        correlation_id="request-002",
    )
    service.record(
        event_type=AuditEventType.AUTHORIZATION,
        action="AUTHORIZE",
        outcome="SUCCESS",
        transaction_id="transaction-002",
        correlation_id="request-003",
    )

    events = service.list_by_transaction("transaction-001")

    assert len(events) == 2
    assert all(
        event.transaction_id == "transaction-001"
        for event in events
    )


def test_list_by_correlation_id_returns_only_matching_events(service):
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

    events = service.list_by_correlation_id("request-001")

    assert len(events) == 2
    assert all(
        event.correlation_id == "request-001"
        for event in events
    )


def test_audit_event_supports_failed_operations(service):
    event = service.record(
        event_type=AuditEventType.SECURITY,
        action="AUTHORIZE",
        outcome="FAILURE",
        correlation_id="request-004",
        detail="Card is not active",
    )

    assert event.event_type == AuditEventType.SECURITY
    assert event.outcome == "FAILURE"
    assert event.detail == "Card is not active"


def test_audit_event_does_not_require_raw_request_payload(service):
    event = service.record(
        event_type=AuditEventType.SECURITY,
        action="VALIDATION",
        outcome="FAILURE",
        correlation_id="request-005",
        detail="Request rejected",
    )

    assert event.audit_event_id is not None
    assert event.detail == "Request rejected"
