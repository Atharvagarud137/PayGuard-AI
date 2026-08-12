import pytest

from app.domain.state_machine import (
    can_transition,
    validate_transition,
    InvalidTransactionTransition,
)
from app.models import TransactionStatus


def test_authorized_to_captured_is_valid():
    assert can_transition(
        TransactionStatus.AUTHORIZED,
        TransactionStatus.CAPTURED,
    )


def test_captured_to_settled_is_valid():
    assert can_transition(
        TransactionStatus.CAPTURED,
        TransactionStatus.SETTLED,
    )


def test_settled_to_partial_refund_is_valid():
    assert can_transition(
        TransactionStatus.SETTLED,
        TransactionStatus.PARTIALLY_REFUNDED,
    )


def test_settled_to_refunded_is_valid():
    assert can_transition(
        TransactionStatus.SETTLED,
        TransactionStatus.REFUNDED,
    )


def test_partial_refund_to_refunded_is_valid():
    assert can_transition(
        TransactionStatus.PARTIALLY_REFUNDED,
        TransactionStatus.REFUNDED,
    )


def test_partial_refund_to_partial_refund_is_valid():
    assert can_transition(
        TransactionStatus.PARTIALLY_REFUNDED,
        TransactionStatus.PARTIALLY_REFUNDED,
    )


@pytest.mark.parametrize(
    "current,target",
    [
        (
                TransactionStatus.AUTHORIZED,
                TransactionStatus.SETTLED,
        ),
        (
                TransactionStatus.AUTHORIZED,
                TransactionStatus.REFUNDED,
        ),
        (
                TransactionStatus.CAPTURED,
                TransactionStatus.REFUNDED,
        ),
        (
                TransactionStatus.SETTLED,
                TransactionStatus.CAPTURED,
        ),
        (
                TransactionStatus.REFUNDED,
                TransactionStatus.CAPTURED,
        ),
        (
                TransactionStatus.REFUNDED,
                TransactionStatus.REFUNDED,
        ),
        (
                TransactionStatus.DECLINED,
                TransactionStatus.CAPTURED,
        ),
    ],
)
def test_invalid_transitions(current, target):
    assert not can_transition(current, target)


def test_validate_transition_raises_for_invalid_transition():
    with pytest.raises(InvalidTransactionTransition):
        validate_transition(
            TransactionStatus.AUTHORIZED,
            TransactionStatus.REFUNDED,
        )