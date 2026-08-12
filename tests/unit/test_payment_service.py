import pytest

from app.models import Transaction, TransactionStatus
from app.repositories.transaction_repository import TransactionRepository
from app.services.payment_service import PaymentService


@pytest.fixture
def payment_service():
    return PaymentService(TransactionRepository())


@pytest.fixture
def authorized_transaction():
    transaction = Transaction(
        card_id="card-123",
        merchant_id="merchant-123",
        authorized_amount=1000,
        status=TransactionStatus.AUTHORIZED,
    )

    TransactionRepository().add(transaction)

    return transaction


@pytest.fixture
def captured_transaction():
    transaction = Transaction(
        card_id="card-123",
        merchant_id="merchant-123",
        authorized_amount=1000,
        captured_amount=1000,
        status=TransactionStatus.CAPTURED,
    )

    TransactionRepository().add(transaction)

    return transaction


@pytest.fixture
def settled_transaction():
    transaction = Transaction(
        card_id="card-123",
        merchant_id="merchant-123",
        authorized_amount=1000,
        captured_amount=1000,
        settled_amount=1000,
        status=TransactionStatus.SETTLED,
    )

    TransactionRepository().add(transaction)

    return transaction


def test_capture_success(payment_service, authorized_transaction):
    result = payment_service.capture(
        authorized_transaction.transaction_id,
        800,
    )

    assert result.status == TransactionStatus.CAPTURED
    assert result.captured_amount == 800


def test_capture_exceeds_authorized_amount(
        payment_service,
        authorized_transaction,
):
    with pytest.raises(
            ValueError,
            match="Capture amount exceeds authorized amount",
    ):
        payment_service.capture(
            authorized_transaction.transaction_id,
            1001,
        )


def test_capture_nonexistent_transaction(payment_service):
    with pytest.raises(
            ValueError,
            match="Transaction not found",
    ):
        payment_service.capture(
            "does-not-exist",
            100,
        )


def test_capture_invalid_state(
        payment_service,
        captured_transaction,
):
    with pytest.raises(
            ValueError,
            match="Transaction is not in AUTHORIZED state",
    ):
        payment_service.capture(
            captured_transaction.transaction_id,
            100,
        )


def test_settle_success(payment_service, captured_transaction):
    result = payment_service.settle(
        captured_transaction.transaction_id
    )

    assert result.status == TransactionStatus.SETTLED
    assert result.settled_amount == 1000


def test_settle_nonexistent_transaction(payment_service):
    with pytest.raises(
            ValueError,
            match="Transaction not found",
    ):
        payment_service.settle("does-not-exist")


def test_settle_invalid_state(
        payment_service,
        authorized_transaction,
):
    with pytest.raises(
            ValueError,
            match="Transaction is not in CAPTURED state",
    ):
        payment_service.settle(
            authorized_transaction.transaction_id
        )


def test_full_refund(payment_service, settled_transaction):
    result, remaining = payment_service.refund(
        settled_transaction.transaction_id,
        1000,
    )

    assert result.status == TransactionStatus.REFUNDED
    assert result.refunded_amount == 1000
    assert remaining == 0


def test_partial_refund(payment_service, settled_transaction):
    result, remaining = payment_service.refund(
        settled_transaction.transaction_id,
        400,
    )

    assert result.status == TransactionStatus.PARTIALLY_REFUNDED
    assert result.refunded_amount == 400
    assert remaining == 600


def test_partial_then_full_refund(
        payment_service,
        settled_transaction,
):
    transaction_id = settled_transaction.transaction_id

    result, remaining = payment_service.refund(
        transaction_id,
        400,
    )

    assert result.status == TransactionStatus.PARTIALLY_REFUNDED
    assert remaining == 600

    result, remaining = payment_service.refund(
        transaction_id,
        600,
    )

    assert result.status == TransactionStatus.REFUNDED
    assert remaining == 0


def test_refund_exceeds_remaining_balance(
        payment_service,
        settled_transaction,
):
    with pytest.raises(
            ValueError,
            match="Refund amount exceeds remaining refundable balance",
    ):
        payment_service.refund(
            settled_transaction.transaction_id,
            1001,
        )


def test_refund_nonexistent_transaction(payment_service):
    with pytest.raises(
            ValueError,
            match="Transaction not found",
    ):
        payment_service.refund(
            "does-not-exist",
            100,
        )


def test_refund_invalid_state(
        payment_service,
        captured_transaction,
):
    with pytest.raises(
            ValueError,
            match="Transaction is not settled",
    ):
        payment_service.refund(
            captured_transaction.transaction_id,
            100,
        )


def test_refund_already_refunded(
        payment_service,
        settled_transaction,
):
    transaction_id = settled_transaction.transaction_id

    payment_service.refund(transaction_id, 1000)

    with pytest.raises(
            ValueError,
            match="Transaction is not settled",
    ):
        payment_service.refund(transaction_id, 100)