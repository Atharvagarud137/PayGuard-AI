def test_capture_success(client, authorized_transaction):
    """Positive case: capturing the full authorized amount should succeed."""

    response = client.post(
        f"/api/v1/transactions/{authorized_transaction['transaction_id']}/capture",
        json={"capture_amount": 1000},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "CAPTURED"
    assert data["captured_amount"] == 1000


def test_capture_partial_amount(client, authorized_transaction):
    """Positive case: capturing less than the authorized amount should succeed."""

    response = client.post(
        f"/api/v1/transactions/{authorized_transaction['transaction_id']}/capture",
        json={"capture_amount": 500},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "CAPTURED"
    assert data["captured_amount"] == 500


def test_capture_exceeds_authorized_amount(
        client,
        authorized_transaction,
):
    """Negative case: capturing more than authorized should be rejected."""

    response = client.post(
        f"/api/v1/transactions/{authorized_transaction['transaction_id']}/capture",
        json={"capture_amount": 5000},
    )

    assert response.status_code == 400


def test_capture_transaction_not_found(client):
    """Negative case: capturing a non-existent transaction should return 404."""

    response = client.post(
        "/api/v1/transactions/non-existent-id/capture",
        json={"capture_amount": 100},
    )

    assert response.status_code == 404


def test_capture_already_captured_transaction(
        client,
        captured_transaction,
        authorized_transaction,
):
    """
    Negative case: capturing a transaction already in CAPTURED state
    should return 409.
    """

    response = client.post(
        f"/api/v1/transactions/{authorized_transaction['transaction_id']}/capture",
        json={"capture_amount": 500},
    )

    assert response.status_code == 409


def test_capture_zero_amount(client, authorized_transaction):
    """Boundary case: capturing zero amount should be rejected by validation."""

    response = client.post(
        f"/api/v1/transactions/{authorized_transaction['transaction_id']}/capture",
        json={"capture_amount": 0},
    )

    assert response.status_code == 422


def test_capture_declined_transaction(client, issued_card):
    """Negative case: capturing a DECLINED transaction should return 409."""

    decline_response = client.post(
        "/api/v1/transactions/authorize",
        json={
            "card_id": issued_card["card_id"],
            "amount": 999999,
            "merchant_id": "merchant-001",
        },
    )

    transaction_id = decline_response.json()["transaction_id"]

    response = client.post(
        f"/api/v1/transactions/{transaction_id}/capture",
        json={"capture_amount": 100},
    )

    assert response.status_code == 409


# ============================================================================
# Capture Idempotency
# ============================================================================

def test_capture_idempotency_replays_same_response(
        client,
        authorized_transaction,
):
    """
    Repeating the same capture request with the same Idempotency-Key
    should return the original response.
    """

    transaction_id = authorized_transaction["transaction_id"]

    headers = {
        "Idempotency-Key": "capture-idempotency-001",
    }

    payload = {
        "capture_amount": 1000,
    }

    first_response = client.post(
        f"/api/v1/transactions/{transaction_id}/capture",
        json=payload,
        headers=headers,
    )

    second_response = client.post(
        f"/api/v1/transactions/{transaction_id}/capture",
        json=payload,
        headers=headers,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    assert second_response.json() == first_response.json()


def test_capture_idempotency_does_not_double_capture(
        client,
        authorized_transaction,
):
    """
    Replaying an idempotent capture must not execute the capture operation
    twice or mutate the transaction a second time.
    """

    transaction_id = authorized_transaction["transaction_id"]

    headers = {
        "Idempotency-Key": "capture-idempotency-002",
    }

    payload = {
        "capture_amount": 1000,
    }

    first_response = client.post(
        f"/api/v1/transactions/{transaction_id}/capture",
        json=payload,
        headers=headers,
    )

    second_response = client.post(
        f"/api/v1/transactions/{transaction_id}/capture",
        json=payload,
        headers=headers,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    lookup_response = client.get(
        f"/api/v1/transactions/{transaction_id}",
    )

    assert lookup_response.status_code == 200

    transaction = lookup_response.json()

    assert transaction["status"] == "CAPTURED"
    assert transaction["captured_amount"] == 1000


def test_capture_idempotency_rejects_different_request(
        client,
        authorized_transaction,
):
    """
    Reusing an Idempotency-Key for a different capture amount must return
    HTTP 409 rather than silently performing another operation.
    """

    transaction_id = authorized_transaction["transaction_id"]

    headers = {
        "Idempotency-Key": "capture-idempotency-003",
    }

    first_response = client.post(
        f"/api/v1/transactions/{transaction_id}/capture",
        json={"capture_amount": 500},
        headers=headers,
    )

    second_response = client.post(
        f"/api/v1/transactions/{transaction_id}/capture",
        json={"capture_amount": 700},
        headers=headers,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409


def test_capture_different_idempotency_keys_create_separate_operations(
        client,
        authorized_transaction,
):
    """
    Different Idempotency-Keys represent different operations.

    The second request reaches the normal transaction-state validation
    and therefore fails because the transaction has already been captured.
    """

    transaction_id = authorized_transaction["transaction_id"]

    first_response = client.post(
        f"/api/v1/transactions/{transaction_id}/capture",
        json={"capture_amount": 500},
        headers={
            "Idempotency-Key": "capture-idempotency-004",
        },
    )

    second_response = client.post(
        f"/api/v1/transactions/{transaction_id}/capture",
        json={"capture_amount": 500},
        headers={
            "Idempotency-Key": "capture-idempotency-005",
        },
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409


def test_capture_without_idempotency_key_preserves_existing_behavior(
        client,
        authorized_transaction,
):
    """
    Capture requests without an Idempotency-Key should continue to use
    the existing non-idempotent behavior.
    """

    transaction_id = authorized_transaction["transaction_id"]

    response = client.post(
        f"/api/v1/transactions/{transaction_id}/capture",
        json={"capture_amount": 1000},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "CAPTURED"
    assert data["captured_amount"] == 1000