import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.storage import storage


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_storage():
    """Runs before every test automatically, ensuring a clean state."""
    storage.reset()
    yield
    storage.reset()


@pytest.fixture
def issued_card(client):
    """Helper fixture: creates a card and returns its response data."""
    response = client.post("/api/v1/cards", json={
        "cardholder_name": "Test User",
        "network": "VISA",
        "initial_balance": 5000,
        "expiry_date": "12/28"
    })
    return response.json()


@pytest.fixture
def authorized_transaction(client, issued_card):
    """Helper fixture: creates an authorized transaction and returns its response data."""
    response = client.post("/api/v1/transactions/authorize", json={
        "card_id": issued_card["card_id"],
        "amount": 1000,
        "merchant_id": "merchant-001"
    })
    return response.json()


@pytest.fixture
def captured_transaction(client, authorized_transaction):
    """Helper fixture: captures the authorized transaction and returns its response data."""
    response = client.post(
        f"/api/v1/transactions/{authorized_transaction['transaction_id']}/capture",
        json={"capture_amount": 1000}
    )
    return response.json()


@pytest.fixture
def settled_transaction(client, captured_transaction):
    """Helper fixture: settles the captured transaction and returns its response data."""
    response = client.post(
        f"/api/v1/transactions/{captured_transaction['transaction_id']}/settle"
    )
    return response.json()