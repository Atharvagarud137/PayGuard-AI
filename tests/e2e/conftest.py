import pytest
from httpx import Client
from playwright.sync_api import Page


@pytest.fixture
def frontend_url() -> str:
    """
    Return the local frontend URL used by E2E tests.
    """
    return "http://localhost:5173"


@pytest.fixture
def backend_url() -> str:
    """
    Return the local backend URL used by E2E tests.
    """
    return "http://localhost:8000"


@pytest.fixture(autouse=True)
def reset_backend_state(
        backend_url: str,
) -> None:
    """
    Reset the running FastAPI application's in-memory state
    before every E2E test.

    The pytest process and FastAPI process are separate Python
    processes. Calling storage.reset() directly from this file
    would therefore reset a different Python process.

    Instead, this fixture calls the backend's dedicated test
    reset endpoint so the actual running FastAPI application
    starts every E2E test with deterministic state.

    The reset clears:

        - cards
        - transactions
        - audit events
        - idempotency records
    """

    with Client(
            base_url=backend_url,
            timeout=10.0,
    ) as client:
        response = client.post(
            "/api/v1/test/reset"
        )

    assert response.status_code == 200, (
        "Failed to reset E2E backend state. "
        f"Expected 200, got {response.status_code}: "
        f"{response.text}"
    )


@pytest.fixture
def dashboard_page(
        page: Page,
        frontend_url: str,
) -> Page:
    """
    Navigate to the PayGuard dashboard before an E2E test.

    The backend state has already been reset by the autouse
    reset_backend_state fixture.

    The frontend is intentionally not started by pytest.
    The test environment must have the Vite development server
    running before E2E tests are executed.
    """

    page.goto(frontend_url)

    page.wait_for_load_state(
        "domcontentloaded"
    )

    return page


@pytest.fixture
def issued_e2e_card(
        backend_url: str,
) -> dict:
    """
    Create a fresh active card through the PayGuard API.

    Backend state is reset automatically before the test by
    reset_backend_state.
    """

    payload = {
        "cardholder_name": "E2E Transaction User",
        "network": "VISA",
        "initial_balance": 5000,
        "expiry_date": "12/28",
    }

    with Client(
            base_url=backend_url,
            timeout=10.0,
    ) as client:
        response = client.post(
            "/api/v1/cards",
            json=payload,
        )

    assert response.status_code == 201, (
        "Failed to create E2E test card. "
        f"Expected 201, got {response.status_code}: "
        f"{response.text}"
    )

    card = response.json()

    assert card["cardholder_name"] == (
        payload["cardholder_name"]
    )

    assert card["network"] == payload["network"]

    assert card["balance"] == (
        payload["initial_balance"]
    )

    assert card["status"] == "ACTIVE"

    assert "card_id" in card

    return card


@pytest.fixture
def authorized_transaction(
        backend_url: str,
        issued_e2e_card: dict,
) -> dict:
    """
    Create an authorized transaction through the PayGuard API.

    The transaction is created against the fresh E2E test card
    created by the issued_e2e_card fixture.

    Because reset_backend_state is autouse, each test that uses
    this fixture begins with clean backend state.
    """

    payload = {
        "card_id": issued_e2e_card["card_id"],
        "amount": 100,
        "merchant_id": "e2e-merchant-001",
    }

    with Client(
            base_url=backend_url,
            timeout=10.0,
    ) as client:
        response = client.post(
            "/api/v1/transactions/authorize",
            json=payload,
        )

    assert response.status_code == 200, (
        "Failed to authorize E2E test transaction. "
        f"Expected 200, got {response.status_code}: "
        f"{response.text}"
    )

    transaction = response.json()

    assert transaction["status"] == "AUTHORIZED"

    assert transaction["authorized_amount"] == 100

    assert "transaction_id" in transaction

    return transaction