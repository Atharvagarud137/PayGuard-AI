from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.database_models import (
    AuditEventDB,
    CardDB,
    IdempotencyRecordDB,
    TransactionDB,
    TransactionEventDB,
)
from app.domain.exceptions import InvalidTransactionStateError
from app.models import (
    Card,
    CardNetwork,
    Transaction,
    TransactionEvent,
    TransactionStatus,
)
from app.repositories.postgres_audit_repository import (
    PostgresAuditRepository,
)
from app.repositories.postgres_card_repository import (
    PostgresCardRepository,
)
from app.repositories.postgres_idempotency_repository import (
    PostgresIdempotencyRepository,
)
from app.repositories.postgres_transaction_repository import (
    PostgresTransactionRepository,
)
from app.services.payment_service import PaymentService


def test_authorization_rolls_back_all_payment_writes_when_idempotency_fails(
        client,
        issued_card,
        db_session,
        monkeypatch,
):
    """
    A failure after the card, transaction, event, audit, and idempotency
    writes have been flushed must leave none of those writes committed.
    """
    original_add = PostgresIdempotencyRepository.add

    def add_then_fail(self, *args, **kwargs):
        original_add(self, *args, **kwargs)
        raise RuntimeError("injected idempotency persistence failure")

    monkeypatch.setattr(
        PostgresIdempotencyRepository,
        "add",
        add_then_fail,
    )

    with pytest.raises(
            RuntimeError,
            match="injected idempotency persistence failure",
    ):
        client.post(
            "/api/v1/transactions/authorize",
            json={
                "card_id": issued_card["card_id"],
                "amount": "1000.00",
                "merchant_id": "merchant-atomicity-test",
            },
            headers={"Idempotency-Key": "atomicity-auth-rollback"},
        )

    db_session.expire_all()

    card = db_session.get(CardDB, issued_card["card_id"])
    assert card is not None
    assert card.balance == Decimal("5000.00")

    assert db_session.scalar(
        select(func.count()).select_from(TransactionDB)
    ) == 0
    assert db_session.scalar(
        select(func.count()).select_from(TransactionEventDB)
    ) == 0
    assert db_session.scalar(
        select(func.count()).select_from(AuditEventDB)
    ) == 0
    assert db_session.scalar(
        select(func.count()).select_from(IdempotencyRecordDB)
    ) == 0


def test_capture_rolls_back_transaction_event_and_audit_when_audit_fails(
        client,
        authorized_transaction,
        db_session,
        monkeypatch,
):
    """
    A failure after the capture event and audit row are flushed must restore
    the transaction to AUTHORIZED and retain only its original history.
    """
    original_add = PostgresAuditRepository.add

    def add_then_fail(self, event):
        original_add(self, event)
        if event.action == "CAPTURE":
            raise RuntimeError("injected capture audit persistence failure")

    monkeypatch.setattr(
        PostgresAuditRepository,
        "add",
        add_then_fail,
    )

    transaction_id = authorized_transaction["transaction_id"]

    with pytest.raises(
            RuntimeError,
            match="injected capture audit persistence failure",
    ):
        client.post(
            f"/api/v1/transactions/{transaction_id}/capture",
            json={"capture_amount": "700.00"},
        )

    db_session.expire_all()

    transaction = db_session.get(TransactionDB, transaction_id)
    assert transaction is not None
    assert transaction.status == TransactionStatus.AUTHORIZED.value
    assert transaction.captured_amount == Decimal("0.00")

    event_statuses = db_session.execute(
        select(TransactionEventDB.status)
        .where(TransactionEventDB.transaction_id == transaction_id)
        .order_by(TransactionEventDB.created_at, TransactionEventDB.id)
    ).scalars().all()
    assert event_statuses == [TransactionStatus.AUTHORIZED.value]

    audit_rows = db_session.execute(
        select(AuditEventDB)
        .where(AuditEventDB.transaction_id == transaction_id)
    ).scalars().all()
    audit_actions = [
        (row.metadata_json or {}).get("action")
        for row in audit_rows
    ]
    assert "AUTHORIZE" in audit_actions
    assert "CAPTURE" not in audit_actions


def _session_factory(engine):
    return sessionmaker(
        bind=engine,
        class_=Session,
        autoflush=False,
        expire_on_commit=False,
    )


def _seed_card(factory, card_id: str, balance: Decimal) -> None:
    card_suffix = int(card_id[-8:], 16) % 10_000
    card = Card(
        card_id=card_id,
        cardholder_name="PayGuard Concurrency Test",
        card_number=f"****-****-****-{card_suffix:04d}",
        network=CardNetwork.VISA,
        balance=balance,
        expiry_date="12/2030",
    )

    with factory() as db:
        PostgresCardRepository(db).add(card)
        db.commit()


def _cleanup_card(factory, card_id: str) -> None:
    """Remove committed records created by an independent-session test."""
    with factory() as db:
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
            delete(TransactionDB).where(
                TransactionDB.card_id == card_id
            )
        )
        db.execute(
            delete(CardDB).where(CardDB.id == card_id)
        )
        db.commit()


def test_concurrent_authorizations_cannot_overdraw_one_card(test_engine):
    """
    Two independent PostgreSQL sessions authorizing 700 against a 1000
    balance must serialize on the card row: one approves and one declines.
    """
    factory = _session_factory(test_engine)
    card_id = str(uuid4())
    _seed_card(factory, card_id, Decimal("1000.00"))
    start_together = Barrier(2)

    def authorize(_):
        with factory() as db:
            start_together.wait(timeout=10)
            service = PaymentService(
                PostgresTransactionRepository(db),
                PostgresCardRepository(db),
            )
            transaction = service.authorize(
                card_id=card_id,
                amount=Decimal("700.00"),
                merchant_id="merchant-concurrency-test",
            )
            db.commit()
            return transaction.status.value

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            statuses = list(executor.map(authorize, range(2)))

        assert statuses.count(TransactionStatus.AUTHORIZED.value) == 1
        assert statuses.count(TransactionStatus.DECLINED.value) == 1

        with factory() as db:
            card = db.get(CardDB, card_id)
            assert card is not None
            assert card.balance == Decimal("300.00")

            transaction_statuses = db.execute(
                select(TransactionDB.status)
                .where(TransactionDB.card_id == card_id)
            ).scalars().all()
            assert sorted(transaction_statuses) == [
                TransactionStatus.AUTHORIZED.value,
                TransactionStatus.DECLINED.value,
            ]

            event_statuses = db.execute(
                select(TransactionEventDB.status)
                .where(
                    TransactionEventDB.transaction_id.in_(
                        select(TransactionDB.id).where(
                            TransactionDB.card_id == card_id
                        )
                    )
                )
            ).scalars().all()
            assert sorted(event_statuses) == [
                TransactionStatus.AUTHORIZED.value,
                TransactionStatus.DECLINED.value,
            ]
    finally:
        _cleanup_card(factory, card_id)


def test_concurrent_captures_apply_only_one_lifecycle_transition(test_engine):
    """
    Two independent PostgreSQL sessions capturing the same authorization
    must serialize on the transaction row. Exactly one capture can succeed.
    """
    factory = _session_factory(test_engine)
    card_id = str(uuid4())
    transaction_id = str(uuid4())
    _seed_card(factory, card_id, Decimal("1000.00"))

    transaction = Transaction(
        transaction_id=transaction_id,
        card_id=card_id,
        merchant_id="merchant-concurrency-test",
        authorized_amount=Decimal("1000.00"),
        status=TransactionStatus.AUTHORIZED,
        history=[
            TransactionEvent(
                status=TransactionStatus.AUTHORIZED,
                detail="Payment authorized",
            )
        ],
    )

    with factory() as db:
        PostgresTransactionRepository(db).add(transaction)
        db.commit()

    start_together = Barrier(2)

    def capture(_):
        with factory() as db:
            start_together.wait(timeout=10)
            service = PaymentService(
                PostgresTransactionRepository(db),
                PostgresCardRepository(db),
            )
            try:
                service.capture(
                    transaction_id=transaction_id,
                    capture_amount=Decimal("700.00"),
                )
                db.commit()
                return "CAPTURED"
            except InvalidTransactionStateError:
                db.rollback()
                return "REJECTED"

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(capture, range(2)))

        assert outcomes.count("CAPTURED") == 1
        assert outcomes.count("REJECTED") == 1

        with factory() as db:
            persisted = db.get(TransactionDB, transaction_id)
            assert persisted is not None
            assert persisted.status == TransactionStatus.CAPTURED.value
            assert persisted.captured_amount == Decimal("700.00")

            event_statuses = db.execute(
                select(TransactionEventDB.status)
                .where(
                    TransactionEventDB.transaction_id == transaction_id
                )
            ).scalars().all()
            assert sorted(event_statuses) == [
                TransactionStatus.AUTHORIZED.value,
                TransactionStatus.CAPTURED.value,
            ]
    finally:
        _cleanup_card(factory, card_id)
