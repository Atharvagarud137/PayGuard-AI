from app.storage import storage
from app.models import CardStatus


def test_authorize_success(client, issued_card):
    """Positive case: sufficient balance should be approved."""
    response = client.post("/api/v1/transactions/authorize", json={
        "card_id": issued_card["card_id"],
        "amount": 1000,
        "merchant_id": "merchant-001"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "AUTHORIZED"
    assert data["authorized_amount"] == 1000
    assert "transaction_id" in data


def test_authorize_insufficient_funds(client, issued_card):
    """Negative case: amount exceeding balance should be declined, not errored."""
    response = client.post("/api/v1/transactions/authorize", json={
        "card_id": issued_card["card_id"],
        "amount": 10000,
        "merchant_id": "merchant-001"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "DECLINED"
    assert data["decline_reason"] == "INSUFFICIENT_FUNDS"


def test_authorize_card_not_found(client):
    """Negative case: authorizing against a non-existent card should return 404."""
    response = client.post("/api/v1/transactions/authorize", json={
        "card_id": "non-existent-card-id",
        "amount": 100,
        "merchant_id": "merchant-001"
    })

    assert response.status_code == 404


def test_authorize_inactive_card(client, issued_card):
    """Negative case: authorizing against an inactive card should return 400."""
    card = storage.get_card(issued_card["card_id"])
    card.status = CardStatus.INACTIVE
    storage.update_card(card)

    response = client.post("/api/v1/transactions/authorize", json={
        "card_id": issued_card["card_id"],
        "amount": 100,
        "merchant_id": "merchant-001"
    })

    assert response.status_code == 400


def test_authorize_exact_balance_amount(client, issued_card):
    """Boundary case: authorizing exactly the available balance should succeed."""
    response = client.post("/api/v1/transactions/authorize", json={
        "card_id": issued_card["card_id"],
        "amount": issued_card["balance"],
        "merchant_id": "merchant-001"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "AUTHORIZED"
    assert data["authorized_amount"] == issued_card["balance"]


def test_authorize_missing_merchant_id(client, issued_card):
    """Negative case: missing merchant_id should be rejected by validation."""
    response = client.post("/api/v1/transactions/authorize", json={
        "card_id": issued_card["card_id"],
        "amount": 100
    })

    assert response.status_code == 422


def test_authorize_zero_amount(client, issued_card):
    """Boundary case: authorizing zero amount should be rejected (must be > 0)."""
    response = client.post("/api/v1/transactions/authorize", json={
        "card_id": issued_card["card_id"],
        "amount": 0,
        "merchant_id": "merchant-001"
    })

    assert response.status_code == 422


# ============================================================================
# Idempotency
# ============================================================================

def test_authorize_idempotency_replays_same_response(client, issued_card):
    """
    Repeating the same authorization request with the same Idempotency-Key
    should return the original response instead of creating another
    transaction.
    """

    headers = {
        "Idempotency-Key": "auth-idempotency-001"
    }

    payload = {
        "card_id": issued_card["card_id"],
        "amount": 1000,
        "merchant_id": "merchant-001"
    }

    first_response = client.post(
        "/api/v1/transactions/authorize",
        json=payload,
        headers=headers,
    )

    second_response = client.post(
        "/api/v1/transactions/authorize",
        json=payload,
        headers=headers,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_data = first_response.json()
    second_data = second_response.json()

    assert first_data == second_data
    assert first_data["status"] == "AUTHORIZED"
    assert first_data["authorized_amount"] == 1000


def test_authorize_idempotency_does_not_double_charge(
        client,
        issued_card,
):
    """
    Repeating an authorization with the same idempotency key should not
    deduct the amount from the card balance more than once.
    """

    headers = {
        "Idempotency-Key": "auth-idempotency-002"
    }

    payload = {
        "card_id": issued_card["card_id"],
        "amount": 1000,
        "merchant_id": "merchant-001"
    }

    initial_balance = issued_card["balance"]

    first_response = client.post(
        "/api/v1/transactions/authorize",
        json=payload,
        headers=headers,
    )

    second_response = client.post(
        "/api/v1/transactions/authorize",
        json=payload,
        headers=headers,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    card = storage.get_card(issued_card["card_id"])

    assert card.balance == initial_balance - 1000


def test_authorize_idempotency_rejects_different_request(
        client,
        issued_card,
):
    """
    Reusing an Idempotency-Key for a different authorization request should
    be rejected with HTTP 409 rather than silently creating a new operation.
    """

    headers = {
        "Idempotency-Key": "auth-idempotency-003"
    }

    first_payload = {
        "card_id": issued_card["card_id"],
        "amount": 1000,
        "merchant_id": "merchant-001"
    }

    second_payload = {
        "card_id": issued_card["card_id"],
        "amount": 2000,
        "merchant_id": "merchant-001"
    }

    first_response = client.post(
        "/api/v1/transactions/authorize",
        json=first_payload,
        headers=headers,
    )

    second_response = client.post(
        "/api/v1/transactions/authorize",
        json=second_payload,
        headers=headers,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409

    data = second_response.json()

    assert (
            data["detail"]
            == "Idempotency-Key has already been used for a different "
               "authorization request"
    )


def test_authorize_different_idempotency_keys_create_separate_operations(
        client,
        issued_card,
):
    """
    Different Idempotency-Keys represent separate authorization operations.
    """

    payload = {
        "card_id": issued_card["card_id"],
        "amount": 1000,
        "merchant_id": "merchant-001"
    }

    first_response = client.post(
        "/api/v1/transactions/authorize",
        json=payload,
        headers={
            "Idempotency-Key": "auth-idempotency-004"
        },
    )

    second_response = client.post(
        "/api/v1/transactions/authorize",
        json=payload,
        headers={
            "Idempotency-Key": "auth-idempotency-005"
        },
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_data = first_response.json()
    second_data = second_response.json()

    assert first_data["status"] == "AUTHORIZED"
    assert second_data["status"] == "AUTHORIZED"

    assert (
            first_data["transaction_id"]
            != second_data["transaction_id"]
    )


def test_authorize_without_idempotency_key_preserves_existing_behavior(
        client,
        issued_card,
):
    """
    Requests without an Idempotency-Key should preserve the existing
    non-idempotent behavior.
    """

    payload = {
        "card_id": issued_card["card_id"],
        "amount": 1000,
        "merchant_id": "merchant-001"
    }

    first_response = client.post(
        "/api/v1/transactions/authorize",
        json=payload,
    )

    second_response = client.post(
        "/api/v1/transactions/authorize",
        json=payload,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_data = first_response.json()
    second_data = second_response.json()

    assert first_data["status"] == "AUTHORIZED"
    assert second_data["status"] == "AUTHORIZED"

    assert (
            first_data["transaction_id"]
            != second_data["transaction_id"]
    )