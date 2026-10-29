
from decimal import Decimal
from typing import Dict, Optional

import pytest

from app.domain.exceptions import (
    CaptureAmountExceededError,
    InvalidTransactionStateError,
    RefundAmountExceededError,
    TransactionNotFoundError,
)
from app.models import (
    Card,
    CardNetwork,
    CardStatus,
    Transaction,
    TransactionEvent,
    TransactionStatus,
)
from app.services.payment_service import PaymentService


class FakeCardRepository:
    """In-memory card repository for isolated service unit tests."""

    def __init__(self) -> None:
        self.cards: Dict[str, Card] = {}

    def add(self, card: Card) -> None:
        self.cards[card.card_id] = card

    def get(self, card_id: str) -> Optional[Card]:
        return self.cards.get(card_id)

    def get_for_update(self, card_id: str) -> Optional[Card]:
        return self.get(card_id)

    def update(self, card: Card) -> None:
        if card.card_id not in self.cards:
            raise ValueError(f"Card '{card.card_id}' does not exist.")
        self.cards[card.card_id] = card

    def exists_with_number(self, card_number: str) -> bool:
        return any(
            card.card_number == card_number
            for card in self.cards.values()
        )


class FakeTransactionRepository:
    """In-memory transaction repository for isolated unit tests."""

    def __init__(self) -> None:
        self.transactions: Dict[str, Transaction] = {}

    def add(self, transaction: Transaction) -> None:
        self.transactions[transaction.transaction_id] = transaction

    def get(self, transaction_id: str) -> Optional[Transaction]:
        return self.transactions.get(transaction_id)

    def get_for_update(
            self,
            transaction_id: str,
    ) -> Optional[Transaction]:
        return self.get(transaction_id)

    def update(self, transaction: Transaction) -> None:
        if transaction.transaction_id not in self.transactions:
            raise ValueError(
                f"Transaction '{transaction.transaction_id}' does not exist."
            )
        self.transactions[transaction.transaction_id] = transaction


@pytest.fixture
def repositories():
    return FakeTransactionRepository(), FakeCardRepository()


@pytest.fixture
def payment_service(repositories):
    transaction_repository, card_repository = repositories
    return PaymentService(transaction_repository, card_repository)


@pytest.fixture
def active_card(repositories):
    _, card_repository = repositories

    card = Card(
        card_id="card-123",
        cardholder_name="Test Customer",
        card_number="411111******1111",
        network=CardNetwork.VISA,
        balance=Decimal("5000.00"),
        status=CardStatus.ACTIVE,
        expiry_date="12/30",
    )
    card_repository.add(card)
    return card


@pytest.fixture
def authorized_transaction(repositories):
    transaction_repository, _ = repositories

    transaction = Transaction(
        transaction_id="transaction-authorized",
        card_id="card-123",
        merchant_id="merchant-123",
        authorized_amount=Decimal("1000.00"),
        status=TransactionStatus.AUTHORIZED,
        history=[
            TransactionEvent(status=TransactionStatus.AUTHORIZED)
        ],
    )
    transaction_repository.add(transaction)
    return transaction


@pytest.fixture
def captured_transaction(repositories):
    transaction_repository, _ = repositories

    transaction = Transaction(
        transaction_id="transaction-captured",
        card_id="card-123",
        merchant_id="merchant-123",
        authorized_amount=Decimal("1000.00"),
        captured_amount=Decimal("1000.00"),
        status=TransactionStatus.CAPTURED,
        history=[
            TransactionEvent(status=TransactionStatus.AUTHORIZED),
            TransactionEvent(status=TransactionStatus.CAPTURED),
        ],
    )
    transaction_repository.add(transaction)
    return transaction


@pytest.fixture
def settled_transaction(repositories):
    transaction_repository, _ = repositories

    transaction = Transaction(
        transaction_id="transaction-settled",
        card_id="card-123",
        merchant_id="merchant-123",
        authorized_amount=Decimal("1000.00"),
        captured_amount=Decimal("1000.00"),
        settled_amount=Decimal("1000.00"),
        status=TransactionStatus.SETTLED,
        history=[
            TransactionEvent(status=TransactionStatus.AUTHORIZED),
            TransactionEvent(status=TransactionStatus.CAPTURED),
            TransactionEvent(status=TransactionStatus.SETTLED),
        ],
    )
    transaction_repository.add(transaction)
    return transaction


def test_authorize_success(payment_service, active_card):
    result = payment_service.authorize(
        card_id=active_card.card_id,
        amount=Decimal("800.00"),
        merchant_id="merchant-123",
    )

    assert result.status == TransactionStatus.AUTHORIZED
    assert result.authorized_amount == Decimal("800.00")


def test_authorize_insufficient_funds(payment_service, active_card):
    result = payment_service.authorize(
        card_id=active_card.card_id,
        amount=Decimal("6000.00"),
        merchant_id="merchant-123",
    )

    assert result.status == TransactionStatus.DECLINED
    assert result.decline_reason == "INSUFFICIENT_FUNDS"
    assert active_card.balance == Decimal("5000.00")


def test_authorize_nonexistent_card(payment_service):
    with pytest.raises(
            TransactionNotFoundError,
            match="Card not found",
    ):
        payment_service.authorize(
            card_id="missing-card",
            amount=Decimal("100.00"),
            merchant_id="merchant-123",
        )


def test_capture_success(payment_service, authorized_transaction):
    result = payment_service.capture(
        authorized_transaction.transaction_id,
        Decimal("800.00"),
    )

    assert result.status == TransactionStatus.CAPTURED
    assert result.captured_amount == Decimal("800.00")


def test_capture_exceeds_authorized_amount(
        payment_service,
        authorized_transaction,
):
    with pytest.raises(CaptureAmountExceededError):
        payment_service.capture(
            authorized_transaction.transaction_id,
            Decimal("1000.01"),
        )


def test_capture_nonexistent_transaction(payment_service):
    with pytest.raises(TransactionNotFoundError):
        payment_service.capture(
            "does-not-exist",
            Decimal("100.00"),
        )


def test_capture_invalid_state(payment_service, captured_transaction):
    with pytest.raises(InvalidTransactionStateError):
        payment_service.capture(
            captured_transaction.transaction_id,
            Decimal("100.00"),
        )


def test_settle_success(payment_service, captured_transaction):
    result = payment_service.settle(
        captured_transaction.transaction_id
    )

    assert result.status == TransactionStatus.SETTLED
    assert result.settled_amount == Decimal("1000.00")


def test_settle_nonexistent_transaction(payment_service):
    with pytest.raises(TransactionNotFoundError):
        payment_service.settle("does-not-exist")


def test_settle_invalid_state(payment_service, authorized_transaction):
    with pytest.raises(InvalidTransactionStateError):
        payment_service.settle(
            authorized_transaction.transaction_id
        )


def test_full_refund(payment_service, settled_transaction):
    result, remaining = payment_service.refund(
        settled_transaction.transaction_id,
        Decimal("1000.00"),
    )

    assert result.status == TransactionStatus.REFUNDED
    assert result.refunded_amount == Decimal("1000.00")
    assert remaining == Decimal("0.00")


def test_partial_refund(payment_service, settled_transaction):
    result, remaining = payment_service.refund(
        settled_transaction.transaction_id,
        Decimal("400.00"),
    )

    assert result.status == TransactionStatus.PARTIALLY_REFUNDED
    assert result.refunded_amount == Decimal("400.00")
    assert remaining == Decimal("600.00")


def test_partial_then_full_refund(
        payment_service,
        settled_transaction,
):
    transaction_id = settled_transaction.transaction_id

    result, remaining = payment_service.refund(
        transaction_id,
        Decimal("400.00"),
    )

    assert result.status == TransactionStatus.PARTIALLY_REFUNDED
    assert remaining == Decimal("600.00")

    result, remaining = payment_service.refund(
        transaction_id,
        Decimal("600.00"),
    )

    assert result.status == TransactionStatus.REFUNDED
    assert remaining == Decimal("0.00")


def test_refund_exceeds_remaining_balance(
        payment_service,
        settled_transaction,
):
    with pytest.raises(RefundAmountExceededError):
        payment_service.refund(
            settled_transaction.transaction_id,
            Decimal("1000.01"),
        )


def test_refund_nonexistent_transaction(payment_service):
    with pytest.raises(TransactionNotFoundError):
        payment_service.refund(
            "does-not-exist",
            Decimal("100.00"),
        )


def test_refund_invalid_state(payment_service, captured_transaction):
    with pytest.raises(InvalidTransactionStateError):
        payment_service.refund(
            captured_transaction.transaction_id,
            Decimal("100.00"),
        )


def test_refund_already_refunded(
        payment_service,
        settled_transaction,
):
    transaction_id = settled_transaction.transaction_id

    payment_service.refund(transaction_id, Decimal("1000.00"))

    with pytest.raises(InvalidTransactionStateError):
        payment_service.refund(transaction_id, Decimal("100.00"))


@pytest.mark.parametrize(
    "amount",
    [
        Decimal("0"),
        Decimal("-1.00"),
        Decimal("NaN"),
        Decimal("Infinity"),
        Decimal("1.001"),
    ],
)
def test_capture_rejects_invalid_amount(
        payment_service,
        authorized_transaction,
        amount,
):
    with pytest.raises(ValueError):
        payment_service.capture(
            authorized_transaction.transaction_id,
            amount,
        )
