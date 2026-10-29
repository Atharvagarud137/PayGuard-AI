import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
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


@pytest.fixture(scope="session", autouse=True)
def create_test_schema(
        test_engine: Engine,
) -> Generator[None, None, None]:
    """
    Create ORM tables for an isolated test database.

    Alembic migrations must be tested separately.
    """
    Base.metadata.create_all(bind=test_engine)

    try:
        yield
    finally:
        Base.metadata.drop_all(bind=test_engine)


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