from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import List, Optional
import uuid

from pydantic import (
    BaseModel,
    Field,
    field_serializer,
    field_validator,
)


# ============================================================================
# Money Validation
# ============================================================================

def validate_money_amount(
        value: Decimal,
) -> Decimal:
    """
    Validate a monetary amount.

    Payment amounts must:
        - remain Decimal values internally
        - contain no more than two decimal places

    Decimal is deliberately used instead of float to avoid precision
    problems in financial calculations.
    """

    if value.as_tuple().exponent < -2:
        raise ValueError(
            "Monetary amounts must have at most two decimal places"
        )

    return value


# ============================================================================
# Card Enums
# ============================================================================

class CardNetwork(str, Enum):
    VISA = "VISA"
    MASTERCARD = "MASTERCARD"
    GENERIC = "GENERIC"


class CardStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    EXPIRED = "EXPIRED"


# ============================================================================
# Transaction Enums
# ============================================================================

class TransactionStatus(str, Enum):
    AUTHORIZED = "AUTHORIZED"
    DECLINED = "DECLINED"
    CAPTURED = "CAPTURED"
    SETTLED = "SETTLED"
    REFUNDED = "REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"


# ============================================================================
# Audit Enums
# ============================================================================

class AuditEventType(str, Enum):
    """
    Categories of security and payment-domain audit events.

    These values are intentionally explicit so audit records can later
    be queried, filtered, aggregated, and consumed by the AI RCA layer.
    """

    AUTHORIZATION = "AUTHORIZATION"
    CAPTURE = "CAPTURE"
    SETTLEMENT = "SETTLEMENT"
    REFUND = "REFUND"
    SECURITY = "SECURITY"


# ============================================================================
# Card Models
# ============================================================================

class CardCreateRequest(BaseModel):
    cardholder_name: str
    network: CardNetwork

    initial_balance: Decimal = Field(
        gt=Decimal("0")
    )

    expiry_date: str

    @field_validator("initial_balance")
    @classmethod
    def validate_initial_balance(
            cls,
            value: Decimal,
    ) -> Decimal:
        return validate_money_amount(value)


class Card(BaseModel):
    card_id: str = Field(
        default_factory=lambda: str(uuid.uuid4())
    )

    cardholder_name: str

    # The application stores only a masked representation.
    card_number: str

    network: CardNetwork

    balance: Decimal = Decimal("0.00")

    status: CardStatus = CardStatus.ACTIVE

    expiry_date: str

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator("balance")
    @classmethod
    def validate_balance(
            cls,
            value: Decimal,
    ) -> Decimal:
        return validate_money_amount(value)

    @field_serializer("balance")
    def serialize_balance(
            self,
            value: Decimal,
    ) -> float:
        """
        Serialize Decimal as a JSON number at the API boundary.

        Decimal remains the internal representation used for monetary
        calculations.
        """

        return float(value)


# ============================================================================
# Transaction Request Models
# ============================================================================

class AuthorizeRequest(BaseModel):
    card_id: str

    amount: Decimal = Field(
        gt=Decimal("0")
    )

    merchant_id: str

    @field_validator("amount")
    @classmethod
    def validate_amount(
            cls,
            value: Decimal,
    ) -> Decimal:
        return validate_money_amount(value)


class CaptureRequest(BaseModel):
    capture_amount: Decimal = Field(
        gt=Decimal("0")
    )

    @field_validator("capture_amount")
    @classmethod
    def validate_capture_amount(
            cls,
            value: Decimal,
    ) -> Decimal:
        return validate_money_amount(value)


class RefundRequest(BaseModel):
    refund_amount: Decimal = Field(
        gt=Decimal("0")
    )

    @field_validator("refund_amount")
    @classmethod
    def validate_refund_amount(
            cls,
            value: Decimal,
    ) -> Decimal:
        return validate_money_amount(value)


# ============================================================================
# Transaction Event
# ============================================================================

class TransactionEvent(BaseModel):
    status: TransactionStatus

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    detail: Optional[str] = None


# ============================================================================
# Transaction Model
# ============================================================================

class Transaction(BaseModel):
    transaction_id: str = Field(
        default_factory=lambda: str(uuid.uuid4())
    )

    card_id: str

    merchant_id: Optional[str] = None

    authorized_amount: Decimal = Decimal("0.00")

    captured_amount: Decimal = Decimal("0.00")

    settled_amount: Decimal = Decimal("0.00")

    refunded_amount: Decimal = Decimal("0.00")

    status: TransactionStatus

    decline_reason: Optional[str] = None

    history: List[TransactionEvent] = Field(
        default_factory=list
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator(
        "authorized_amount",
        "captured_amount",
        "settled_amount",
        "refunded_amount",
    )
    @classmethod
    def validate_transaction_amount(
            cls,
            value: Decimal,
    ) -> Decimal:
        return validate_money_amount(value)

    @field_serializer(
        "authorized_amount",
        "captured_amount",
        "settled_amount",
        "refunded_amount",
    )
    def serialize_amounts(
            self,
            value: Decimal,
    ) -> float:
        """
        Serialize Decimal monetary values as JSON numbers.

        Internal calculations continue to use Decimal.
        """

        return float(value)


# ============================================================================
# Audit Event Model
# ============================================================================

class AuditEvent(BaseModel):
    audit_event_id: str = Field(
        default_factory=lambda: str(uuid.uuid4())
    )

    event_type: AuditEventType

    action: str

    outcome: str

    correlation_id: Optional[str] = None

    transaction_id: Optional[str] = None

    card_id: Optional[str] = None

    merchant_id: Optional[str] = None

    amount: Optional[Decimal] = None

    detail: Optional[str] = None

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator("amount")
    @classmethod
    def validate_audit_amount(
            cls,
            value: Optional[Decimal],
    ) -> Optional[Decimal]:
        if value is None:
            return None

        return validate_money_amount(value)

    @field_serializer("amount")
    def serialize_amount(
            self,
            value: Optional[Decimal],
    ) -> Optional[float]:
        """
        Serialize audit monetary values at the API boundary.
        """

        if value is None:
            return None

        return float(value)