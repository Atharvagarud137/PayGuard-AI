from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import List, Optional
import uuid

from pydantic import BaseModel, Field, field_serializer


class CardNetwork(str, Enum):
    VISA = "VISA"
    MASTERCARD = "MASTERCARD"
    GENERIC = "GENERIC"


class CardStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    EXPIRED = "EXPIRED"


class TransactionStatus(str, Enum):
    AUTHORIZED = "AUTHORIZED"
    DECLINED = "DECLINED"
    CAPTURED = "CAPTURED"
    SETTLED = "SETTLED"
    REFUNDED = "REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"


# ---------------------------------------------------------------------------
# Card Models
# ---------------------------------------------------------------------------

class CardCreateRequest(BaseModel):
    cardholder_name: str
    network: CardNetwork
    initial_balance: Decimal = Field(gt=Decimal("0"))
    expiry_date: str


class Card(BaseModel):
    card_id: str = Field(
        default_factory=lambda: str(uuid.uuid4())
    )
    cardholder_name: str
    card_number: str
    network: CardNetwork
    balance: Decimal = Decimal("0.00")
    status: CardStatus = CardStatus.ACTIVE
    expiry_date: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_serializer("balance")
    def serialize_balance(self, value: Decimal) -> float:
        """
        Serialize Decimal as a JSON number at the API boundary.

        Decimal remains the internal representation used for monetary
        calculations. The conversion to float exists only to preserve
        the existing JSON API contract.
        """
        return float(value)


# ---------------------------------------------------------------------------
# Transaction Request Models
# ---------------------------------------------------------------------------

class AuthorizeRequest(BaseModel):
    card_id: str
    amount: Decimal = Field(gt=Decimal("0"))
    merchant_id: str


class CaptureRequest(BaseModel):
    capture_amount: Decimal = Field(gt=Decimal("0"))


class RefundRequest(BaseModel):
    refund_amount: Decimal = Field(gt=Decimal("0"))


# ---------------------------------------------------------------------------
# Transaction Event
# ---------------------------------------------------------------------------

class TransactionEvent(BaseModel):
    status: TransactionStatus
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    detail: Optional[str] = None


# ---------------------------------------------------------------------------
# Transaction Model
# ---------------------------------------------------------------------------

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

    @field_serializer(
        "authorized_amount",
        "captured_amount",
        "settled_amount",
        "refunded_amount",
    )
    def serialize_amounts(self, value: Decimal) -> float:
        """
        Serialize Decimal monetary values as JSON numbers.

        Internal calculations continue to use Decimal. This conversion
        exists only at the API serialization boundary.
        """
        return float(value)