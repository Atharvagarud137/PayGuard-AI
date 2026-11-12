from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Event
from time import monotonic, sleep
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session

from app.database import get_db
from app.database_models import (
    AuditEventDB,
    CardDB,
    IdempotencyRecordDB,
    TransactionDB,
    TransactionEventDB,
)
from app.main import app
from app.models import Card, CardNetwork
from app.repositories.postgres_card_repository import (
    PostgresCardRepository,
)
from app.repositories.postgres_transaction_repository import (
    PostgresTransactionRepository,
)
from app.services.payment_service import PaymentService


def _seed_payment_state(engine, stage: str) -> tuple[str, str | None]:
    card_id = str(uuid4())
    suffix = int(card_id[-8:], 16) % 10_000

    with Session(engine, autoflush=False, expire_on_commit=False) as db:
        PostgresCardRepository(db).add(
            Card(
                card_id=card_id,
                cardholder_name="PayGuard Idempotency Test",
                card_number=f"****-****-****-{suffix:04d}",
                network=CardNetwork.VISA,
                balance=Decimal("5000.00"),
                expiry_date="12/2030",
            )
        )

        transaction_id = None
        if stage != "authorization":
            service = PaymentService(
                PostgresTransactionRepository(db),
                PostgresCardRepository(db),
            )
            transaction = service.authorize(
                card_id=card_id,
                amount=Decimal("1000.00"),
                merchant_id="merchant-idempotency-test",
            )
            transaction_id = transaction.transaction_id

            if stage in ("capture", "settlement", "refund"):
                service.capture(
                    transaction_id,
                    Decimal("1000.00"),
                )

            if stage in ("settlement", "refund"):
                service.settle(transaction_id)

        db.commit()

    return card_id, transaction_id


def _wait_for_advisory_lock(engine, timeout: float = 10.0) -> None:
    deadline = monotonic() + timeout
    statement = text(
        """
        SELECT count(*)
        FROM pg_stat_activity
        WHERE datname = current_database()
          AND wait_event_type = 'Lock'
          AND wait_event = 'advisory'
          AND query ILIKE '%pg_advisory_xact_lock%'
        """
    )

    with Session(engine) as db:
        while monotonic() < deadline:
            waiting = db.execute(statement).scalar_one()
            if waiting:
                return
            sleep(0.02)

    raise AssertionError(
        "The duplicate request did not wait on the PostgreSQL "
        "idempotency advisory lock."
    )


def _run_concurrent_duplicate_requests(
        engine,
        monkeypatch,
        *,
        service_method: str,
        path: str,
        payload: dict | None,
        idempotency_key: str,
):
    first_operation_entered = Event()
    release_first_operation = Event()
    original_method = getattr(PaymentService, service_method)

    def pause_first_operation(self, *args, **kwargs):
        first_operation_entered.set()
        if not release_first_operation.wait(timeout=15):
            raise TimeoutError("Timed out waiting to release first request")
        return original_method(self, *args, **kwargs)

    monkeypatch.setattr(
        PaymentService,
        service_method,
        pause_first_operation,
    )

    def override_get_db():
        db = Session(
            engine,
            autoflush=False,
            expire_on_commit=False,
        )
        try:
            yield db
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db

    def send_request():
        with TestClient(app) as client:
            kwargs = {
                "headers": {"Idempotency-Key": idempotency_key},
            }
            if payload is not None:
                kwargs["json"] = payload
            return client.post(path, **kwargs)

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            first = executor.submit(send_request)
            assert first_operation_entered.wait(timeout=10), (
                "The first request did not reach the payment operation."
            )

            second = executor.submit(send_request)
            _wait_for_advisory_lock(engine)
            release_first_operation.set()

            first_response = first.result(timeout=20)
            second_response = second.result(timeout=20)
            return first_response, second_response
    finally:
        release_first_operation.set()
        if previous_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous_override


def _cleanup_payment_state(engine, card_id: str, key: str) -> None:
    with Session(engine) as db:
        transaction_ids = select(TransactionDB.id).where(
            TransactionDB.card_id == card_id
        )
        db.execute(
            delete(AuditEventDB).where(
                AuditEventDB.transaction_id.in_(transaction_ids)
            )
        )
        db.execute(
            delete(TransactionEventDB).where(
                TransactionEventDB.transaction_id.in_(transaction_ids)
            )
        )
        db.execute(
            delete(IdempotencyRecordDB).where(
                IdempotencyRecordDB.idempotency_key == key
            )
        )
        db.execute(
            delete(TransactionDB).where(
                TransactionDB.card_id == card_id
            )
        )
        db.execute(delete(CardDB).where(CardDB.id == card_id))
        db.commit()


def _assert_one_replay_record_and_audit(
        engine,
        transaction_id: str,
        idempotency_key: str,
) -> None:
    with Session(engine) as db:
        replay_count = db.scalar(
            select(func.count())
            .select_from(IdempotencyRecordDB)
            .where(
                IdempotencyRecordDB.idempotency_key == idempotency_key
            )
        )
        audit_count = db.scalar(
            select(func.count())
            .select_from(AuditEventDB)
            .where(AuditEventDB.transaction_id == transaction_id)
        )

    assert replay_count == 1
    assert audit_count == 1


def test_concurrent_duplicate_authorizations_execute_once(
        test_engine,
        monkeypatch,
):
    card_id, _ = _seed_payment_state(test_engine, "authorization")
    key = f"concurrent-auth-{uuid4()}"

    try:
        first, second = _run_concurrent_duplicate_requests(
            test_engine,
            monkeypatch,
            service_method="authorize",
            path="/api/v1/transactions/authorize",
            payload={
                "card_id": card_id,
                "amount": "1000.00",
                "merchant_id": "merchant-idempotency-test",
            },
            idempotency_key=key,
        )

        assert first.status_code == second.status_code == 200
        assert first.json() == second.json()
        transaction_id = first.json()["transaction_id"]

        with Session(test_engine) as db:
            card = db.get(CardDB, card_id)
            transaction_count = db.scalar(
                select(func.count())
                .select_from(TransactionDB)
                .where(TransactionDB.card_id == card_id)
            )

        assert card is not None
        assert card.balance == Decimal("4000.00")
        assert transaction_count == 1
        _assert_one_replay_record_and_audit(
            test_engine,
            transaction_id,
            key,
        )
    finally:
        _cleanup_payment_state(test_engine, card_id, key)


def test_concurrent_duplicate_captures_execute_once(
        test_engine,
        monkeypatch,
):
    card_id, transaction_id = _seed_payment_state(test_engine, "capture")
    key = f"concurrent-capture-{uuid4()}"

    try:
        first, second = _run_concurrent_duplicate_requests(
            test_engine,
            monkeypatch,
            service_method="capture",
            path=f"/api/v1/transactions/{transaction_id}/capture",
            payload={"capture_amount": "700.00"},
            idempotency_key=key,
        )

        assert first.status_code == second.status_code == 200
        assert first.json() == second.json()

        with Session(test_engine) as db:
            transaction = db.get(TransactionDB, transaction_id)
            captured_events = db.scalar(
                select(func.count())
                .select_from(TransactionEventDB)
                .where(
                    TransactionEventDB.transaction_id == transaction_id,
                    TransactionEventDB.status == "CAPTURED",
                )
            )

        assert transaction is not None
        assert transaction.status == "CAPTURED"
        assert transaction.captured_amount == Decimal("700.00")
        assert captured_events == 1
        _assert_one_replay_record_and_audit(
            test_engine,
            transaction_id,
            key,
        )
    finally:
        _cleanup_payment_state(test_engine, card_id, key)


def test_concurrent_duplicate_settlements_execute_once(
        test_engine,
        monkeypatch,
):
    card_id, transaction_id = _seed_payment_state(test_engine, "settlement")
    key = f"concurrent-settlement-{uuid4()}"

    try:
        first, second = _run_concurrent_duplicate_requests(
            test_engine,
            monkeypatch,
            service_method="settle",
            path=f"/api/v1/transactions/{transaction_id}/settle",
            payload=None,
            idempotency_key=key,
        )

        assert first.status_code == second.status_code == 200
        assert first.json() == second.json()

        with Session(test_engine) as db:
            transaction = db.get(TransactionDB, transaction_id)
            settled_events = db.scalar(
                select(func.count())
                .select_from(TransactionEventDB)
                .where(
                    TransactionEventDB.transaction_id == transaction_id,
                    TransactionEventDB.status == "SETTLED",
                )
            )

        assert transaction is not None
        assert transaction.status == "SETTLED"
        assert transaction.settled_amount == Decimal("1000.00")
        assert settled_events == 1
        _assert_one_replay_record_and_audit(
            test_engine,
            transaction_id,
            key,
        )
    finally:
        _cleanup_payment_state(test_engine, card_id, key)


def test_concurrent_duplicate_refunds_execute_once(
        test_engine,
        monkeypatch,
):
    card_id, transaction_id = _seed_payment_state(test_engine, "refund")
    key = f"concurrent-refund-{uuid4()}"

    try:
        first, second = _run_concurrent_duplicate_requests(
            test_engine,
            monkeypatch,
            service_method="refund",
            path=f"/api/v1/transactions/{transaction_id}/refund",
            payload={"refund_amount": "400.00"},
            idempotency_key=key,
        )

        assert first.status_code == second.status_code == 200
        assert first.json() == second.json()

        with Session(test_engine) as db:
            transaction = db.get(TransactionDB, transaction_id)
            refund_events = db.scalar(
                select(func.count())
                .select_from(TransactionEventDB)
                .where(
                    TransactionEventDB.transaction_id == transaction_id,
                    TransactionEventDB.status == "PARTIALLY_REFUNDED",
                )
            )

        assert transaction is not None
        assert transaction.status == "PARTIALLY_REFUNDED"
        assert transaction.refunded_amount == Decimal("400.00")
        assert refund_events == 1
        _assert_one_replay_record_and_audit(
            test_engine,
            transaction_id,
            key,
        )
    finally:
        _cleanup_payment_state(test_engine, card_id, key)
