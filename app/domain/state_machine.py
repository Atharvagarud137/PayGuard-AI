from app.models import TransactionStatus


class InvalidTransactionTransition(Exception):
    """Raised when a transaction attempts an invalid state transition."""


ALLOWED_TRANSITIONS: dict[TransactionStatus, set[TransactionStatus]] = {
    TransactionStatus.AUTHORIZED: {
        TransactionStatus.CAPTURED,
    },
    TransactionStatus.DECLINED: set(),
    TransactionStatus.CAPTURED: {
        TransactionStatus.SETTLED,
    },
    TransactionStatus.SETTLED: {
        TransactionStatus.PARTIALLY_REFUNDED,
        TransactionStatus.REFUNDED,
    },
    TransactionStatus.PARTIALLY_REFUNDED: {
        TransactionStatus.PARTIALLY_REFUNDED,
        TransactionStatus.REFUNDED,
    },
    TransactionStatus.REFUNDED: set(),
}


def can_transition(
        current: TransactionStatus,
        target: TransactionStatus,
) -> bool:
    """Return True when the requested state transition is valid."""
    return target in ALLOWED_TRANSITIONS.get(current, set())


def validate_transition(
        current: TransactionStatus,
        target: TransactionStatus,
) -> None:
    """
    Validate a transaction state transition.

    Raises:
        InvalidTransactionTransition:
            When the requested transition is not allowed.
    """
    if not can_transition(current, target):
        raise InvalidTransactionTransition(
            f"Invalid transaction transition: "
            f"{current.value} -> {target.value}"
        )