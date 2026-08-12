def test_issue_card_success(client):
    """Positive case: valid card creation should succeed."""
    response = client.post("/api/v1/cards", json={
        "cardholder_name": "Atharva Garud",
        "network": "VISA",
        "initial_balance": 5000,
        "expiry_date": "12/28"
    })

    assert response.status_code == 201
    data = response.json()
    assert data["cardholder_name"] == "Atharva Garud"
    assert data["network"] == "VISA"
    assert data["balance"] == 5000
    assert data["status"] == "ACTIVE"
    assert "card_id" in data
    assert data["card_number"].startswith("****-****-****-")


def test_issue_card_missing_required_field(client):
    """Negative case: missing cardholder_name should be rejected."""
    response = client.post("/api/v1/cards", json={
        "network": "VISA",
        "initial_balance": 5000,
        "expiry_date": "12/28"
    })

    assert response.status_code == 422


def test_issue_card_invalid_network(client):
    """Negative case: invalid network type should be rejected."""
    response = client.post("/api/v1/cards", json={
        "cardholder_name": "Atharva Garud",
        "network": "AMEX",
        "initial_balance": 5000,
        "expiry_date": "12/28"
    })

    assert response.status_code == 422


def test_issue_card_zero_initial_balance(client):
    """Boundary case: initial balance of zero should be rejected (must be > 0)."""
    response = client.post("/api/v1/cards", json={
        "cardholder_name": "Atharva Garud",
        "network": "VISA",
        "initial_balance": 0,
        "expiry_date": "12/28"
    })

    assert response.status_code == 422


def test_issue_card_negative_initial_balance(client):
    """Boundary case: negative initial balance should be rejected."""
    response = client.post("/api/v1/cards", json={
        "cardholder_name": "Atharva Garud",
        "network": "VISA",
        "initial_balance": -100,
        "expiry_date": "12/28"
    })

    assert response.status_code == 422


def test_issue_multiple_cards_have_unique_ids(client):
    """Ensures each issued card gets a unique card_id."""
    response1 = client.post("/api/v1/cards", json={
        "cardholder_name": "User One",
        "network": "MASTERCARD",
        "initial_balance": 1000,
        "expiry_date": "01/27"
    })
    response2 = client.post("/api/v1/cards", json={
        "cardholder_name": "User Two",
        "network": "MASTERCARD",
        "initial_balance": 1000,
        "expiry_date": "01/27"
    })

    assert response1.json()["card_id"] != response2.json()["card_id"]