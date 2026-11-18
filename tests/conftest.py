import os
from collections.abc import Generator

import pytest

# Ensure the app registers test-only routes before app.main is imported.
os.environ.setdefault("PAYGUARD_ENV", "test")
os.environ.setdefault("PAYGUARD_ENABLE_TEST_ENDPOINTS", "true")
os.environ.setdefault(
    "PAYGUARD_TEST_RESET_TOKEN",
    "payguard-test-reset-token-2026-phase4",
)
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import get_db
from app.main import app


def _get_test_database_url() -> str:
    """Return the dedicated PostgreSQL test database URL."""
    database_url = (
            os.getenv("TEST_DATABASE_URL")
            or os.getenv("DATABASE_URL")
    )

    if not database_url:
        raise RuntimeError(
            "A test database URL is required. Set TEST_DATABASE_URL "
            "to a dedicated PostgreSQL test database."
        )

    if not database_url.startswith("postgresql+psycopg://"):
        raise RuntimeError(
            "Tests require a PostgreSQL URL using the "
            "postgresql+psycopg driver."
        )

    return database_url


@pytest.fixture(scope="session")
def test_engine() -> Generator[Engine, None, None]:
    """Create an engine for the test session."""
    engine = create_engine(
        _get_test_database_url(),
        pool_pre_ping=True,
    )

    try:
        yield engine
    finally:
        engine.dispose()



@pytest.fixture(scope="session")
def migration_engine() -> Generator[Engine, None, None]:
    """
    Open a separate maintenance connection for migration-owner-only tests.

    This connection is reserved for tests that deliberately exercise owner
    powers, such as disabling a trigger to simulate out-of-band tampering.
    Application code and ordinary API tests must use test_engine instead.
    """
    migration_url = os.getenv("PAYGUARD_MIGRATION_DATABASE_URL")
    if not migration_url:
        raise RuntimeError(
            "PAYGUARD_MIGRATION_DATABASE_URL is required for maintenance tests."
        )

    engine = create_engine(migration_url, pool_pre_ping=True)
    try:
        yield engine
    finally:
        engine.dispose()

@pytest.fixture(scope="session", autouse=True)
def verify_migrated_test_schema(
        test_engine: Engine,
) -> None:
    """
    Verify migrations created the schema before tests start.

    The runtime role must not own tables or have schema DDL privileges.
    Test databases are disposable and are recreated by the test environment.
    """
    if not inspect(test_engine).has_table("alembic_version"):
        raise RuntimeError(
            "Test database is not migrated. Run Alembic with "
            "PAYGUARD_MIGRATION_DATABASE_URL before pytest."
        )

    with test_engine.connect() as connection:
        version = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one_or_none()

    if version is None:
        raise RuntimeError(
            "Test database has no Alembic revision. Run migrations first."
        )


@pytest.fixture
def db_session(
        test_engine: Engine,
) -> Generator[Session, None, None]:
    """
    Provide a database session isolated by an outer transaction.

    Application commits are contained within the outer transaction,
    which is rolled back when the test finishes.
    """
    connection = test_engine.connect()
    outer_transaction = connection.begin()

    testing_session_local = sessionmaker(
        bind=connection,
        class_=Session,
        autoflush=False,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )

    session = testing_session_local()

    try:
        yield session
    finally:
        session.close()

        if outer_transaction.is_active:
            outer_transaction.rollback()

        connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create a test client using the isolated test database session."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        if previous_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous_override


@pytest.fixture
def issued_card(client: TestClient) -> dict:
    """Issue a card through the API for the current test."""
    response = client.post(
        "/api/v1/cards",
        json={
            "cardholder_name": "PayGuard Test User",
            "network": "VISA",
            "initial_balance": "5000.00",
            "expiry_date": "12/2030",
        },
    )

    assert response.status_code == 201, (
        f"Card setup failed: HTTP {response.status_code}: "
        f"{response.text}"
    )

    card = response.json()

    assert card.get("card_id"), (
        f"Card response is missing card_id: {card}"
    )

    return card


@pytest.fixture
def authorized_transaction(
        client: TestClient,
        issued_card: dict,
) -> dict:
    """Create an authorized transaction through the API."""
    response = client.post(
        "/api/v1/transactions/authorize",
        json={
            "card_id": issued_card["card_id"],
            "amount": "1000.00",
            "merchant_id": "merchant-test-001",
        },
    )

    assert response.status_code == 200, (
        f"Authorization setup failed: HTTP {response.status_code}: "
        f"{response.text}"
    )

    transaction = response.json()

    assert transaction.get("transaction_id"), (
        f"Authorization response is missing transaction_id: "
        f"{transaction}"
    )
    assert transaction["status"] == "AUTHORIZED", (
        f"Expected AUTHORIZED transaction, received: {transaction}"
    )

    return transaction


@pytest.fixture
def captured_transaction(
        client: TestClient,
        authorized_transaction: dict,
) -> dict:
    """Create a captured transaction through the API."""
    transaction_id = authorized_transaction["transaction_id"]

    response = client.post(
        f"/api/v1/transactions/{transaction_id}/capture",
        json={"capture_amount": "1000.00"},
    )

    assert response.status_code == 200, (
        f"Capture setup failed: HTTP {response.status_code}: "
        f"{response.text}"
    )

    transaction = response.json()

    assert transaction["status"] == "CAPTURED", (
        f"Expected CAPTURED transaction, received: {transaction}"
    )

    return transaction

@pytest.fixture
def settled_transaction(
        client: TestClient,
        captured_transaction: dict,
) -> dict:
    """Create a settled transaction through the API."""
    transaction_id = captured_transaction["transaction_id"]
    response = client.post(
        f"/api/v1/transactions/{transaction_id}/settle"
    )

    assert response.status_code == 200, (
        f"Settlement setup failed: HTTP {response.status_code}: "
        f"{response.text}"
    )

    transaction = response.json()
    assert transaction["status"] == "SETTLED", (
        f"Expected SETTLED transaction, received: {transaction}"
    )
    return transaction
