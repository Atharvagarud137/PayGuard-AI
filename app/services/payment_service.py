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
    CardStatus,
    Transaction,
    TransactionEvent,
    TransactionStatus,
)
from app.repositories.interfaces import (
    CardRepositoryProtocol,
    TransactionRepositoryProtocol,
)


class PaymentService:
    """
    Contains payment transaction business logic.

    The service layer owns payment lifecycle operations and delegates
    persistence to repository contracts.

    The service depends on repository protocols rather than concrete
    persistence implementations, allowing the underlying storage mechanism
    to change without changing payment business logic.

    Transaction lifecycle operations that mutate an existing transaction
    retrieve it through get_for_update() so PostgreSQL-backed repositories
    can serialize concurrent updates using row-level locking.
    """

    def __init__(
            self,
            repository: TransactionRepositoryProtocol,
            card_repository: CardRepositoryProtocol,
    ) -> None:
        self.repository = repository
        self.card_repository = card_repository

    # -----------------------------------------------------------------------
    # Transaction Lookup
    # -----------------------------------------------------------------------

    def get_transaction(
            self,
            transaction_id: str,
    ) -> Transaction | None:
        """
        Retrieve a transaction by ID.

        This is a read-only operation and therefore does not acquire a
        database row lock.

        Returns:
            The transaction if found, otherwise None.
        """
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
        Authorize a payment against a card.

        Authorization business rules belong to the payment service rather
        than the API layer.

        Behavior:
        - Missing cards result in a transaction lookup failure.
        - Inactive cards cannot be authorized.
        - Insufficient funds create a DECLINED transaction.
        - Successful authorization deducts the authorized amount from the
          card balance and creates an AUTHORIZED transaction.

        The card is retrieved using get_for_update() so a PostgreSQL-backed
        repository can acquire a row-level lock before the balance is read
        and modified. This prevents concurrent authorization operations from
        spending the same available balance.

        Returns:
            The newly created payment transaction.

        Raises:
            TransactionNotFoundError:
                If the requested card does not exist.

            InvalidTransactionStateError:
                If the card is not active.
        """

        card = self.card_repository.get_for_update(card_id)

        if not card:
            raise TransactionNotFoundError(
                "Card not found"
            )

        if card.status != CardStatus.ACTIVE:
            raise InvalidTransactionStateError(
                "Card is not active"
            )

        transaction = Transaction(
            card_id=card.card_id,
            merchant_id=merchant_id,
            authorized_amount=amount,
            status=TransactionStatus.AUTHORIZED,
        )

        if card.balance < amount:
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

        card.balance -= amount
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

        A transaction must be in AUTHORIZED state before capture.
        The capture amount cannot exceed the authorized amount.

        The transaction is retrieved using get_for_update() so a
        PostgreSQL-backed repository can acquire a row-level lock before
        validating and modifying the transaction.
        """

        transaction = self.repository.get_for_update(transaction_id)

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

        The transaction is retrieved using get_for_update() so a
        PostgreSQL-backed repository can acquire a row-level lock before
        validating and modifying the transaction.
        """

        transaction = self.repository.get_for_update(transaction_id)

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

        The transaction is retrieved using get_for_update() so a
        PostgreSQL-backed repository can serialize concurrent refund
        operations against the same transaction.

        Returns:
            A tuple containing the updated transaction and the remaining
            refundable balance.
        """

        transaction = self.repository.get_for_update(transaction_id)

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