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