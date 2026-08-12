class PaymentError(ValueError):
    """Base exception for payment-domain errors."""


class TransactionNotFoundError(PaymentError):
    """Raised when a transaction cannot be found."""


class InvalidTransactionStateError(PaymentError):
    """Raised when a transaction is in an invalid state for an operation."""


class CaptureAmountExceededError(PaymentError):
    """Raised when capture amount exceeds authorized amount."""


class RefundAmountExceededError(PaymentError):
    """Raised when refund amount exceeds the remaining refundable balance."""