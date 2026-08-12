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