def test_capture_success(client, authorized_transaction):
    """Positive case: capturing the full authorized amount should succeed."""
    response = client.post(
        f"/api/v1/transactions/{authorized_transaction['transaction_id']}/capture",
        json={"capture_amount": 1000}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CAPTURED"
    assert data["captured_amount"] == 1000


def test_capture_partial_amount(client, authorized_transaction):
    """Positive case: capturing less than the authorized amount should succeed."""
    response = client.post(
        f"/api/v1/transactions/{authorized_transaction['transaction_id']}/capture",
        json={"capture_amount": 500}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CAPTURED"
    assert data["captured_amount"] == 500


def test_capture_exceeds_authorized_amount(client, authorized_transaction):
    """Negative case: capturing more than authorized should be rejected."""
    response = client.post(
        f"/api/v1/transactions/{authorized_transaction['transaction_id']}/capture",
        json={"capture_amount": 5000}
    )

    assert response.status_code == 400


def test_capture_transaction_not_found(client):
    """Negative case: capturing a non-existent transaction should return 404."""
    response = client.post(
        "/api/v1/transactions/non-existent-id/capture",
        json={"capture_amount": 100}
    )

    assert response.status_code == 404


def test_capture_already_captured_transaction(client, captured_transaction, authorized_transaction):
    """Negative case: capturing a transaction already in CAPTURED state should return 409."""
    response = client.post(
        f"/api/v1/transactions/{authorized_transaction['transaction_id']}/capture",
        json={"capture_amount": 500}
    )

    assert response.status_code == 409


def test_capture_zero_amount(client, authorized_transaction):
    """Boundary case: capturing zero amount should be rejected by validation."""
    response = client.post(
        f"/api/v1/transactions/{authorized_transaction['transaction_id']}/capture",
        json={"capture_amount": 0}
    )

    assert response.status_code == 422


def test_capture_declined_transaction(client, issued_card):
    """Negative case: capturing a DECLINED transaction should return 409."""
    decline_response = client.post("/api/v1/transactions/authorize", json={
        "card_id": issued_card["card_id"],
        "amount": 999999,
        "merchant_id": "merchant-001"
    })
    transaction_id = decline_response.json()["transaction_id"]

    response = client.post(
        f"/api/v1/transactions/{transaction_id}/capture",
        json={"capture_amount": 100}
    )

    assert response.status_code == 409