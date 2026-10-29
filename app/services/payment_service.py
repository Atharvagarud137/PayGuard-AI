
from decimal import Decimal, InvalidOperation

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
    CardStatus,
    Transaction,
    TransactionEvent,
    TransactionStatus,
    validate_money_amount,
)
from app.repositories.interfaces import (
    CardRepositoryProtocol,
    TransactionRepositoryProtocol,
)


class PaymentService:
    """
    Application service containing payment lifecycle business logic.

    The service depends on repository protocols rather than concrete
    persistence implementations. This allows in-memory and PostgreSQL
    repositories to share the same business rules.

    Operations that mutate existing records use get_for_update() so
    PostgreSQL repositories can acquire row-level locks before reading
    and modifying the relevant state.

    Transaction boundaries remain the caller's responsibility. The caller
    must commit a successful operation or roll back a failed operation.
    """

    def __init__(
            self,
            repository: TransactionRepositoryProtocol,
            card_repository: CardRepositoryProtocol,
    ) -> None:
        self.repository = repository
        self.card_repository = card_repository

    # -----------------------------------------------------------------------
    # Monetary Validation
    # -----------------------------------------------------------------------

    @staticmethod
    def _normalize_amount(
            amount: Decimal,
            *,
            field_name: str,
            allow_zero: bool = False,
    ) -> Decimal:
        """
        Normalize and validate a monetary amount.

        Decimal(str(amount)) avoids importing binary floating-point
        representation errors when callers supply compatible numeric values.
        """
        try:
            normalized = (
                amount
                if isinstance(amount, Decimal)
                else Decimal(str(amount))
            )
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError(
                f"{field_name} must be a valid monetary amount"
            ) from exc

        try:
            normalized = validate_money_amount(normalized)
        except (ValueError, AttributeError) as exc:
            raise ValueError(
                f"{field_name} must be finite and have at most "
                "two decimal places"
            ) from exc

        if allow_zero:
            if normalized < Decimal("0"):
                raise ValueError(
                    f"{field_name} cannot be negative"
                )
        elif normalized <= Decimal("0"):
            raise ValueError(
                f"{field_name} must be greater than zero"
            )

        return normalized

    # -----------------------------------------------------------------------
    # Transaction Lookup
    # -----------------------------------------------------------------------

    def get_transaction(
            self,
            transaction_id: str,
    ) -> Transaction | None:
        """Retrieve a transaction without acquiring a mutation lock."""
        return self.repository.get(transaction_id)

    # -----------------------------------------------------------------------
    # Authorization
    # -----------------------------------------------------------------------

    def authorize(
            self,
            card_id: str,
            amount: Decimal,
            merchant_id: str,
    ) -> Transaction:
        """
        Authorize a payment against an active card.

        A successful authorization deducts the authorized amount from the
        mock card balance and creates an AUTHORIZED transaction.

        Insufficient funds create a DECLINED transaction without changing
        the card balance.

        The card is locked before its balance is read and modified when
        the repository supports PostgreSQL row-level locking.
        """
        amount = self._normalize_amount(
            amount,
            field_name="Authorization amount",
        )

        card = self.card_repository.get_for_update(card_id)

        if card is None:
            raise TransactionNotFoundError("Card not found")

        if card.status != CardStatus.ACTIVE:
            raise InvalidTransactionStateError("Card is not active")

        balance = self._normalize_amount(
            card.balance,
            field_name="Card balance",
            allow_zero=True,
        )

        transaction = Transaction(
            card_id=card.card_id,
            merchant_id=merchant_id,
            authorized_amount=amount,
            status=TransactionStatus.AUTHORIZED,
        )

        if balance < amount:
            transaction.status = TransactionStatus.DECLINED
            transaction.decline_reason = "INSUFFICIENT_FUNDS"

            transaction.history.append(
                TransactionEvent(
                    status=TransactionStatus.DECLINED,
                    detail="Authorization declined: insufficient funds",
                )
            )

            self.repository.add(transaction)
            return transaction

        card.balance = balance - amount
        self.card_repository.update(card)

        transaction.history.append(
            TransactionEvent(
                status=TransactionStatus.AUTHORIZED,
                detail="Payment authorized",
            )
        )

        self.repository.add(transaction)
        return transaction

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

        This implementation supports one capture per transaction.
        Partial capture followed by additional captures is not supported.
        """
        capture_amount = self._normalize_amount(
            capture_amount,
            field_name="Capture amount",
        )

        transaction = self.repository.get_for_update(transaction_id)

        if transaction is None:
            raise TransactionNotFoundError("Transaction not found")

        if transaction.status != TransactionStatus.AUTHORIZED:
            raise InvalidTransactionStateError(
                "Transaction is not in AUTHORIZED state"
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
        """Settle a captured transaction for its captured amount."""
        transaction = self.repository.get_for_update(transaction_id)

        if transaction is None:
            raise TransactionNotFoundError("Transaction not found")

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

        Supports partial refunds and repeated refunds until the full
        settled amount has been refunded.

        Refund operations acquire a transaction row lock through the
        repository so concurrent refunds cannot independently calculate
        their limits from the same stale transaction state.
        """
        refund_amount = self._normalize_amount(
            refund_amount,
            field_name="Refund amount",
        )

        transaction = self.repository.get_for_update(transaction_id)

        if transaction is None:
            raise TransactionNotFoundError("Transaction not found")

        if transaction.status not in (
                TransactionStatus.SETTLED,
                TransactionStatus.PARTIALLY_REFUNDED,
        ):
            raise InvalidTransactionStateError(
                "Transaction is not settled"
            )

        settled_amount = self._normalize_amount(
            transaction.settled_amount,
            field_name="Settled amount",
            allow_zero=True,
        )
        refunded_amount = self._normalize_amount(
            transaction.refunded_amount,
            field_name="Previously refunded amount",
            allow_zero=True,
        )

        if refunded_amount > settled_amount:
            raise InvalidTransactionStateError(
                "Previously refunded amount exceeds settled amount"
            )

        remaining = settled_amount - refunded_amount

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

        self._validate_transition(
            current_status=transaction.status,
            target_status=target_status,
            expected_state=(
                f"Invalid refund transition: "
                f"{transaction.status} -> {target_status}"
            ),
        )

        transaction.refunded_amount = refunded_amount + refund_amount
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
    # State Transition Helper
    # -----------------------------------------------------------------------

    @staticmethod
    def _validate_transition(
            current_status: TransactionStatus,
            target_status: TransactionStatus,
            expected_state: str,
    ) -> None:
        """Translate state-machine failures into service-layer exceptions."""
        try:
            validate_transition(
                current_status,
                target_status,
            )
        except InvalidTransactionTransition as exc:
            raise InvalidTransactionStateError(
                expected_state,
            ) from exc
