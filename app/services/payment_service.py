from decimal import Decimal

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
    """
    Contains payment transaction business logic.

    The service layer owns transaction lifecycle operations and delegates
    persistence to the TransactionRepository. It does not access storage
    directly.
    """

    def __init__(
            self,
            repository: TransactionRepository,
    ) -> None:
        self.repository = repository

    # -----------------------------------------------------------------------
    # Transaction Lookup
    # -----------------------------------------------------------------------

    def get_transaction(
            self,
            transaction_id: str,
    ) -> Transaction | None:
        """
        Retrieve a transaction by ID.

        Returns:
            The transaction if found, otherwise None.
        """
        return self.repository.get(transaction_id)

    # -----------------------------------------------------------------------
    # Capture
    # -----------------------------------------------------------------------

    def capture(
            self,
            transaction_id: str,
            capture_amount: Decimal,
    ) -> Transaction:
        """
        Capture an authorized transaction.

        A transaction must be in AUTHORIZED state before capture.
        The capture amount cannot exceed the authorized amount.
        """

        transaction = self.repository.get(transaction_id)

        if not transaction:
            raise TransactionNotFoundError(
                "Transaction not found"
            )

        if transaction.status != TransactionStatus.AUTHORIZED:
            raise InvalidTransactionStateError(
                "Transaction is not in AUTHORIZED state"
            )

        if capture_amount <= Decimal("0"):
            raise ValueError(
                "Capture amount must be greater than zero"
            )

        if capture_amount > transaction.authorized_amount:
            raise CaptureAmountExceededError(
                "Capture amount exceeds authorized amount"
            )

        self._validate_transition(
            current_status=transaction.status,
            target_status=TransactionStatus.CAPTURED,
            expected_state="Transaction is not in AUTHORIZED state",
        )

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

    # -----------------------------------------------------------------------
    # Settlement
    # -----------------------------------------------------------------------

    def settle(
            self,
            transaction_id: str,
    ) -> Transaction:
        """
        Settle a captured transaction.

        A transaction must be in CAPTURED state before settlement.
        The settled amount is equal to the captured amount.
        """

        transaction = self.repository.get(transaction_id)

        if not transaction:
            raise TransactionNotFoundError(
                "Transaction not found"
            )

        if transaction.status != TransactionStatus.CAPTURED:
            raise InvalidTransactionStateError(
                "Transaction is not in CAPTURED state"
            )

        self._validate_transition(
            current_status=transaction.status,
            target_status=TransactionStatus.SETTLED,
            expected_state="Transaction is not in CAPTURED state",
        )

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

    # -----------------------------------------------------------------------
    # Refund
    # -----------------------------------------------------------------------

    def refund(
            self,
            transaction_id: str,
            refund_amount: Decimal,
    ) -> tuple[Transaction, Decimal]:
        """
        Refund a settled transaction.

        Supports:
        - Full refunds
        - Partial refunds
        - Multiple partial refunds
        - Partial refund followed by a final full refund

        Returns:
            A tuple containing the updated transaction and the remaining
            refundable balance.
        """

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

        if refund_amount <= Decimal("0"):
            raise ValueError(
                "Refund amount must be greater than zero"
            )

        remaining = (
                transaction.settled_amount
                - transaction.refunded_amount
        )

        if refund_amount > remaining:
            raise RefundAmountExceededError(
                "Refund amount exceeds remaining refundable balance"
            )

        remaining_after = remaining - refund_amount

        target_status = (
            TransactionStatus.REFUNDED
            if remaining_after == Decimal("0")
            else TransactionStatus.PARTIALLY_REFUNDED
        )

        # Validate the state transition BEFORE mutating the transaction.
        self._validate_transition(
            current_status=transaction.status,
            target_status=target_status,
            expected_state=(
                f"Invalid refund transition: "
                f"{transaction.status} -> {target_status}"
            ),
        )

        transaction.refunded_amount += refund_amount
        transaction.status = target_status

        transaction.history.append(
            TransactionEvent(
                status=target_status,
                detail=f"Refunded {refund_amount}",
            )
        )

        self.repository.update(transaction)

        return transaction, remaining_after

    # -----------------------------------------------------------------------
    # Internal Helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _validate_transition(
            current_status: TransactionStatus,
            target_status: TransactionStatus,
            expected_state: str,
    ) -> None:
        """
        Validate a transaction state transition and translate the domain
        state-machine exception into the service-layer exception exposed
        to callers.
        """

        try:
            validate_transition(
                current_status,
                target_status,
            )
        except InvalidTransactionTransition as exc:
            raise InvalidTransactionStateError(
                expected_state
            ) from exc