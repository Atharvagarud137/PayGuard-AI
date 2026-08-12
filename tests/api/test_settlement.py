def test_settle_success(client, captured_transaction):
    """Positive case: settling a captured transaction should succeed."""
    response = client.post(
        f"/api/v1/transactions/{captured_transaction['transaction_id']}/settle"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SETTLED"
    assert "settled_at" in data


def test_settle_transaction_not_captured(client, authorized_transaction):
    """Negative case: settling a transaction still in AUTHORIZED state should return 409."""
    response = client.post(
        f"/api/v1/transactions/{authorized_transaction['transaction_id']}/settle"
    )

    assert response.status_code == 409


def test_settle_already_settled_transaction(client, settled_transaction, captured_transaction):
    """Negative case: settling an already-settled transaction should return 409."""
    response = client.post(
        f"/api/v1/transactions/{captured_transaction['transaction_id']}/settle"
    )

    assert response.status_code == 409


def test_settle_transaction_not_found(client):
    """Negative case: settling a non-existent transaction should return 404."""
    response = client.post("/api/v1/transactions/non-existent-id/settle")

    assert response.status_code == 404


def test_settle_simulated_timeout(client, captured_transaction):
    """Simulated failure case: settlement with X-Simulate-Failure: TIMEOUT should return 504."""
    response = client.post(
        f"/api/v1/transactions/{captured_transaction['transaction_id']}/settle",
        headers={"X-Simulate-Failure": "TIMEOUT"}
    )

    assert response.status_code == 504


def test_settle_simulated_network_error(client, captured_transaction):
    """Simulated failure case: settlement with X-Simulate-Failure: NETWORK_ERROR should return 502."""
    response = client.post(
        f"/api/v1/transactions/{captured_transaction['transaction_id']}/settle",
        headers={"X-Simulate-Failure": "NETWORK_ERROR"}
    )

    assert response.status_code == 502