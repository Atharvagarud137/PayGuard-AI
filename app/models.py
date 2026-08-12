from enum import Enum
from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid


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


class CardCreateRequest(BaseModel):
    cardholder_name: str
    network: CardNetwork
    initial_balance: float = Field(gt=0)
    expiry_date: str


class Card(BaseModel):
    card_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    cardholder_name: str
    card_number: str
    network: CardNetwork
    balance: float
    status: CardStatus = CardStatus.ACTIVE
    expiry_date: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AuthorizeRequest(BaseModel):
    card_id: str
    amount: float = Field(gt=0)
    merchant_id: str


class CaptureRequest(BaseModel):
    capture_amount: float = Field(gt=0)


class RefundRequest(BaseModel):
    refund_amount: float = Field(gt=0)


class TransactionEvent(BaseModel):
    status: TransactionStatus
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    detail: Optional[str] = None


class Transaction(BaseModel):
    transaction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    card_id: str
    merchant_id: Optional[str] = None
    authorized_amount: float = 0
    captured_amount: float = 0
    settled_amount: float = 0
    refunded_amount: float = 0
    status: TransactionStatus
    decline_reason: Optional[str] = None
    history: List[TransactionEvent] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))