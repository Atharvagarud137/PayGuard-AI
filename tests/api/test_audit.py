def test_authorization_creates_audit_event(
        client,
        issued_card,
):
    """
    Successful authorization should create an audit record.
    """

    response = client.post(
        "/api/v1/transactions/authorize",
        json={
            "card_id": issued_card["card_id"],
            "amount": 1000,
            "merchant_id": "merchant-001",
        },
    )

    assert response.status_code == 200

    transaction_id = response.json()["transaction_id"]

    # Audit endpoint will be added when API wiring is completed.
    audit_response = client.get(
        f"/api/v1/audit/transactions/{transaction_id}"
    )

    assert audit_response.status_code == 200

    events = audit_response.json()

    assert len(events) >= 1

    authorization_events = [
        event
        for event in events
        if event["action"] == "AUTHORIZE"
    ]

    assert len(authorization_events) == 1

    event = authorization_events[0]

    assert event["outcome"] == "SUCCESS"
    assert event["transaction_id"] == transaction_id


def test_declined_authorization_creates_audit_event(
        client,
        issued_card,
):
    """
    A declined authorization should also create an audit record.
    """

    response = client.post(
        "/api/v1/transactions/authorize",
        json={
            "card_id": issued_card["card_id"],
            "amount": 999999,
            "merchant_id": "merchant-001",
        },
    )

    assert response.status_code == 200

    transaction_id = response.json()["transaction_id"]

    audit_response = client.get(
        f"/api/v1/audit/transactions/{transaction_id}"
    )

    assert audit_response.status_code == 200

    events = audit_response.json()

    authorization_events = [
        event
        for event in events
        if event["action"] == "AUTHORIZE"
    ]

    assert len(authorization_events) == 1

    event = authorization_events[0]

    assert event["outcome"] == "DECLINED"
    assert event["transaction_id"] == transaction_id


def test_capture_creates_audit_event(
        client,
        authorized_transaction,
):
    """
    Successful capture should create an audit record.
    """

    transaction_id = authorized_transaction["transaction_id"]

    response = client.post(
        f"/api/v1/transactions/{transaction_id}/capture",
        json={
            "capture_amount": 1000,
        },
    )

    assert response.status_code == 200

    audit_response = client.get(
        f"/api/v1/audit/transactions/{transaction_id}"
    )

    assert audit_response.status_code == 200

    events = audit_response.json()

    capture_events = [
        event
        for event in events
        if event["action"] == "CAPTURE"
    ]

    assert len(capture_events) == 1

    event = capture_events[0]

    assert event["outcome"] == "SUCCESS"
    assert event["transaction_id"] == transaction_id


def test_audit_events_contain_no_raw_card_number(
        client,
        issued_card,
):
    """
    Audit responses must never expose raw card numbers.

    The current mock system stores only masked card numbers, but the
    audit layer should independently avoid recording card numbers.
    """

    response = client.post(
        "/api/v1/transactions/authorize",
        json={
            "card_id": issued_card["card_id"],
            "amount": 100,
            "merchant_id": "merchant-001",
        },
    )

    assert response.status_code == 200

    transaction_id = response.json()["transaction_id"]

    audit_response = client.get(
        f"/api/v1/audit/transactions/{transaction_id}"
    )

    assert audit_response.status_code == 200

    events = audit_response.json()

    serialized_events = str(events)

    assert issued_card["card_number"] not in serialized_events


def test_audit_integrity_endpoint_reports_a_valid_chain(
        client,
        issued_card,
):
    authorization = client.post(
        "/api/v1/transactions/authorize",
        json={
            "card_id": issued_card["card_id"],
            "amount": 100,
            "merchant_id": "merchant-audit-integrity",
        },
    )
    assert authorization.status_code == 200

    response = client.get("/api/v1/audit/integrity")

    assert response.status_code == 200
    assert response.json()["valid"] is True
    assert response.json()["event_count"] >= 1
    assert response.json()["first_invalid_sequence"] is None


def test_audit_rows_reject_updates_and_deletes(
        client,
        issued_card,
        db_session,
):
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    import pytest

    authorization = client.post(
        "/api/v1/transactions/authorize",
        json={
            "card_id": issued_card["card_id"],
            "amount": 100,
            "merchant_id": "merchant-audit-immutable",
        },
    )
    assert authorization.status_code == 200

    audit_event_id = db_session.execute(
        text(
            "SELECT id FROM audit_events "
            "ORDER BY chain_sequence DESC LIMIT 1"
        )
    ).scalar_one()

    with pytest.raises(DBAPIError):
        with db_session.begin_nested():
            db_session.execute(
                text(
                    "UPDATE audit_events SET message='tampered' "
                    "WHERE id=:event_id"
                ),
                {"event_id": audit_event_id},
            )

    with pytest.raises(DBAPIError):
        with db_session.begin_nested():
            db_session.execute(
                text("DELETE FROM audit_events WHERE id=:event_id"),
                {"event_id": audit_event_id},
            )


def test_audit_hash_chain_detects_out_of_band_tampering(
        client,
        issued_card,
        db_session,
):
    from sqlalchemy import text

    from app.repositories.postgres_audit_repository import (
        PostgresAuditRepository,
    )

    authorization = client.post(
        "/api/v1/transactions/authorize",
        json={
            "card_id": issued_card["card_id"],
            "amount": 100,
            "merchant_id": "merchant-audit-tamper",
        },
    )
    assert authorization.status_code == 200

    db_session.execute(
        text(
            "ALTER TABLE audit_events "
            "DISABLE TRIGGER audit_events_prevent_mutation"
        )
    )
    db_session.execute(
        text(
            "UPDATE audit_events SET message='out-of-band modification' "
            "WHERE chain_sequence=1"
        )
    )
    db_session.execute(
        text(
            "ALTER TABLE audit_events "
            "ENABLE TRIGGER audit_events_prevent_mutation"
        )
    )

    result = PostgresAuditRepository(db_session).verify_integrity()

    assert result["valid"] is False
    assert result["first_invalid_sequence"] == 1


def test_test_reset_clears_audit_events_using_test_only_exception(
        client,
        issued_card,
):
    authorization = client.post(
        "/api/v1/transactions/authorize",
        json={
            "card_id": issued_card["card_id"],
            "amount": 100,
            "merchant_id": "merchant-audit-reset",
        },
    )
    assert authorization.status_code == 200

    before = client.get("/api/v1/audit/integrity")
    assert before.json()["event_count"] >= 1

    from app.config import settings

    reset = client.post(
        "/api/v1/test/reset",
        headers={"X-Test-Reset-Token": settings.test_reset_token},
    )
    assert reset.status_code == 200

    after = client.get("/api/v1/audit/integrity")
    assert after.status_code == 200
    assert after.json() == {
        "valid": True,
        "event_count": 0,
        "first_invalid_sequence": None,
    }
