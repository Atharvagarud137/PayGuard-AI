from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Event
from time import monotonic, sleep
from uuid import uuid4

import pytest
from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session

from app.database_models import (
    AuditEventDB,
    CardDB,
    IdempotencyRecordDB,
    TransactionDB,
    TransactionEventDB,
)
from app.main import (
    authorize_transaction,
    capture_transaction,
    refund_transaction,
    settle_transaction,
)
from app.models import (
    AuthorizeRequest,
    CaptureRequest,
    Card,
    CardNetwork,
    RefundRequest,
)
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
        FROM pg_locks
        WHERE locktype = 'advisory'
          AND granted = false
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
        request_factory,
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

    def send_request():
        with Session(
                engine,
                autoflush=False,
                expire_on_commit=False,
        ) as db:
            return request_factory(db)

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(send_request)
        second = None

        try:
            assert first_operation_entered.wait(timeout=10), (
                "The first request did not reach the payment operation."
            )

            second = executor.submit(send_request)
            _wait_for_advisory_lock(engine)
        finally:
            # Always release the first transaction before the executor waits
            # for worker shutdown, including when the lock assertion fails.
            release_first_operation.set()

        first_result = first.result(timeout=20)
        assert second is not None
        second_result = second.result(timeout=20)
        return first_result, second_result

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
        def request_factory(db):
            return authorize_transaction(
                request=AuthorizeRequest(
                    card_id=card_id,
                    amount=Decimal("1000.00"),
                    merchant_id="merchant-idempotency-test",
                ),
                x_simulate_failure=None,
                idempotency_key=key,
                correlation_id=None,
                db=db,
            )

        first, second = _run_concurrent_duplicate_requests(
            test_engine,
            monkeypatch,
            service_method="authorize",
            request_factory=request_factory,
            idempotency_key=key,
        )

        assert first == second
        transaction_id = first["transaction_id"]

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
        def request_factory(db):
            return capture_transaction(
                transaction_id=transaction_id,
                request=CaptureRequest(
                    capture_amount=Decimal("700.00"),
                ),
                x_simulate_failure=None,
                idempotency_key=key,
                correlation_id=None,
                db=db,
            )

        first, second = _run_concurrent_duplicate_requests(
            test_engine,
            monkeypatch,
            service_method="capture",
            request_factory=request_factory,
            idempotency_key=key,
        )

        assert first == second

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
        def request_factory(db):
            return settle_transaction(
                transaction_id=transaction_id,
                x_simulate_failure=None,
                idempotency_key=key,
                correlation_id=None,
                db=db,
            )

        first, second = _run_concurrent_duplicate_requests(
            test_engine,
            monkeypatch,
            service_method="settle",
            request_factory=request_factory,
            idempotency_key=key,
        )

        assert first == second

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
        def request_factory(db):
            return refund_transaction(
                transaction_id=transaction_id,
                request=RefundRequest(
                    refund_amount=Decimal("400.00"),
                ),
                x_simulate_failure=None,
                idempotency_key=key,
                correlation_id=None,
                db=db,
            )

        first, second = _run_concurrent_duplicate_requests(
            test_engine,
            monkeypatch,
            service_method="refund",
            request_factory=request_factory,
            idempotency_key=key,
        )

        assert first == second

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
