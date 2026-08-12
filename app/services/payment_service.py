from app.domain.exceptions import (
    CaptureAmountExceededError,
    InvalidTransactionStateError,
    RefundAmountExceededError,
    TransactionNotFoundError,
)
from app.domain.state_machine import (
    InvalidTransactionTransition,
    validate_transition,
)
from app.models import (
    Transaction,
    TransactionEvent,
    TransactionStatus,
)
from app.repositories.transaction_repository import TransactionRepository


class PaymentService:
    """Contains payment transaction business logic."""

    def __init__(self, repository: TransactionRepository):
        self.repository = repository

    def get_transaction(
            self,
            transaction_id: str,
    ) -> Transaction | None:
        return self.repository.get(transaction_id)

    def capture(
            self,
            transaction_id: str,
            capture_amount: float,
    ) -> Transaction:
        transaction = self.repository.get(transaction_id)

        if not transaction:
            raise TransactionNotFoundError(
                "Transaction not found"
            )

        if transaction.status != TransactionStatus.AUTHORIZED:
            raise InvalidTransactionStateError(
                "Transaction is not in AUTHORIZED state"
            )

        if capture_amount > transaction.authorized_amount:
            raise CaptureAmountExceededError(
                "Capture amount exceeds authorized amount"
            )

        try:
            validate_transition(
                transaction.status,
                TransactionStatus.CAPTURED,
            )
        except InvalidTransactionTransition as exc:
            raise InvalidTransactionStateError(
                "Transaction is not in AUTHORIZED state"
            ) from exc

        transaction.captured_amount = capture_amount
        transaction.status = TransactionStatus.CAPTURED

        transaction.history.append(
            TransactionEvent(
                status=TransactionStatus.CAPTURED,
                detail="Amount captured",
            )
        )

        self.repository.update(transaction)

        return transaction

    def settle(
            self,
            transaction_id: str,
    ) -> Transaction:
        transaction = self.repository.get(transaction_id)

        if not transaction:
            raise TransactionNotFoundError(
                "Transaction not found"
            )

        if transaction.status != TransactionStatus.CAPTURED:
            raise InvalidTransactionStateError(
                "Transaction is not in CAPTURED state"
            )

        try:
            validate_transition(
                transaction.status,
                TransactionStatus.SETTLED,
            )
        except InvalidTransactionTransition as exc:
            raise InvalidTransactionStateError(
                "Transaction is not in CAPTURED state"
            ) from exc

        transaction.settled_amount = transaction.captured_amount
        transaction.status = TransactionStatus.SETTLED

        transaction.history.append(
            TransactionEvent(
                status=TransactionStatus.SETTLED,
                detail="Transaction settled",
            )
        )

        self.repository.update(transaction)

        return transaction

    def refund(
            self,
            transaction_id: str,
            refund_amount: float,
    ) -> tuple[Transaction, float]:
        transaction = self.repository.get(transaction_id)

        if not transaction:
            raise TransactionNotFoundError(
                "Transaction not found"
            )

        if transaction.status not in (
                TransactionStatus.SETTLED,
                TransactionStatus.PARTIALLY_REFUNDED,
        ):
            raise InvalidTransactionStateError(
                "Transaction is not settled"
            )

        remaining = (
                transaction.settled_amount
                - transaction.refunded_amount
        )

        if refund_amount > remaining:
            raise RefundAmountExceededError(
                "Refund amount exceeds remaining refundable balance"
            )

        transaction.refunded_amount += refund_amount

        remaining_after = (
                transaction.settled_amount
                - transaction.refunded_amount
        )

        target_status = (
            TransactionStatus.REFUNDED
            if remaining_after == 0
            else TransactionStatus.PARTIALLY_REFUNDED
        )

        try:
            validate_transition(
                transaction.status,
                target_status,
            )
        except InvalidTransactionTransition as exc:
            raise InvalidTransactionStateError(
                f"Invalid refund transition: "
                f"{transaction.status} -> {target_status}"
            ) from exc

        transaction.status = target_status

        transaction.history.append(
            TransactionEvent(
                status=target_status,
                detail=f"Refunded {refund_amount}",
            )
        )

        self.repository.update(transaction)

        return transaction, remaining_after