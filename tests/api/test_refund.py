def test_refund_full_amount(client, settled_transaction):
    """Positive case: refund the full settled amount."""
    transaction_id = settled_transaction["transaction_id"]
    settled_amount = 1000

    response = client.post(
        f"/api/v1/transactions/{transaction_id}/refund",
        json={"refund_amount": settled_amount}
    )

    assert response.status_code == 200

    data = response.json()

    assert data["transaction_id"] == transaction_id
    assert data["status"] == "REFUNDED"
    assert data["remaining_balance"] == 0
    assert "refund_id" in data


def test_refund_partial_amount(client, settled_transaction):
    """Positive case: partially refund a settled transaction."""
    transaction_id = settled_transaction["transaction_id"]
    settled_amount = 1000
    refund_amount = 500

    response = client.post(
        f"/api/v1/transactions/{transaction_id}/refund",
        json={"refund_amount": refund_amount}
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "PARTIALLY_REFUNDED"
    assert data["remaining_balance"] == settled_amount - refund_amount


def test_refund_partial_then_full(client, settled_transaction):
    """Positive case: partial refund followed by refunding the remaining balance."""
    transaction_id = settled_transaction["transaction_id"]
    settled_amount = 1000

    first_response = client.post(
        f"/api/v1/transactions/{transaction_id}/refund",
        json={"refund_amount": 500}
    )

    assert first_response.status_code == 200
    assert first_response.json()["status"] == "PARTIALLY_REFUNDED"
    assert first_response.json()["remaining_balance"] == 500

    second_response = client.post(
        f"/api/v1/transactions/{transaction_id}/refund",
        json={"refund_amount": 500}
    )

    assert second_response.status_code == 200

    data = second_response.json()

    assert data["status"] == "REFUNDED"
    assert data["remaining_balance"] == 0


def test_refund_multiple_partial_amounts(client, settled_transaction):
    """Positive case: multiple partial refunds."""
    transaction_id = settled_transaction["transaction_id"]

    first_response = client.post(
        f"/api/v1/transactions/{transaction_id}/refund",
        json={"refund_amount": 250}
    )

    assert first_response.status_code == 200
    assert first_response.json()["status"] == "PARTIALLY_REFUNDED"
    assert first_response.json()["remaining_balance"] == 750

    second_response = client.post(
        f"/api/v1/transactions/{transaction_id}/refund",
        json={"refund_amount": 250}
    )

    assert second_response.status_code == 200
    assert second_response.json()["status"] == "PARTIALLY_REFUNDED"
    assert second_response.json()["remaining_balance"] == 500


def test_refund_exceeds_remaining_balance(client, settled_transaction):
    """Negative case: refund amount exceeding remaining balance returns 400."""
    transaction_id = settled_transaction["transaction_id"]

    response = client.post(
        f"/api/v1/transactions/{transaction_id}/refund",
        json={"refund_amount": 1001}
    )

    assert response.status_code == 400
    assert "exceeds" in response.json()["detail"].lower()


def test_refund_not_settled(client, captured_transaction):
    """Negative case: refunding a transaction that has not settled returns 409."""
    response = client.post(
        f"/api/v1/transactions/{captured_transaction['transaction_id']}/refund",
        json={"refund_amount": 100}
    )

    assert response.status_code == 409


def test_refund_already_fully_refunded(client, settled_transaction):
    """Negative case: a fully refunded transaction cannot be refunded again."""
    transaction_id = settled_transaction["transaction_id"]

    first_response = client.post(
        f"/api/v1/transactions/{transaction_id}/refund",
        json={"refund_amount": 1000}
    )

    assert first_response.status_code == 200
    assert first_response.json()["status"] == "REFUNDED"

    second_response = client.post(
        f"/api/v1/transactions/{transaction_id}/refund",
        json={"refund_amount": 1}
    )

    assert second_response.status_code == 409


def test_refund_transaction_not_found(client):
    """Negative case: refunding a non-existent transaction returns 404."""
    response = client.post(
        "/api/v1/transactions/non-existent-id/refund",
        json={"refund_amount": 100}
    )

    assert response.status_code == 404


def test_refund_zero_amount(client, settled_transaction):
    """Boundary case: zero refund is rejected by request validation."""
    response = client.post(
        f"/api/v1/transactions/{settled_transaction['transaction_id']}/refund",
        json={"refund_amount": 0}
    )

    assert response.status_code == 422


def test_refund_negative_amount(client, settled_transaction):
    """Boundary case: negative refund is rejected by request validation."""
    response = client.post(
        f"/api/v1/transactions/{settled_transaction['transaction_id']}/refund",
        json={"refund_amount": -10}
    )

    assert response.status_code == 422