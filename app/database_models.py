
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ============================================================================
# Card Persistence Model
# ============================================================================

class CardDB(Base):
    """PostgreSQL persistence model for mock payment cards."""

    __tablename__ = "cards"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    card_number: Mapped[str] = mapped_column(
        String(19),
        nullable=False,
        unique=True,
        index=True,
    )

    cardholder_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    network: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    expiry_date: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    transactions: Mapped[list["TransactionDB"]] = relationship(
        "TransactionDB",
        back_populates="card",
    )

    __table_args__ = (
        CheckConstraint(
            "balance >= 0",
            name="ck_cards_balance_non_negative",
        ),
    )


# ============================================================================
# Transaction Persistence Model
# ============================================================================

class TransactionDB(Base):
    """PostgreSQL persistence model for payment transactions."""

    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    card_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("cards.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    merchant_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    authorized_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    captured_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    settled_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    refunded_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    decline_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    card: Mapped["CardDB"] = relationship(
        "CardDB",
        back_populates="transactions",
    )

    events: Mapped[list["TransactionEventDB"]] = relationship(
        "TransactionEventDB",
        back_populates="transaction",
        cascade="all, delete-orphan",
        order_by="TransactionEventDB.created_at",
    )

    audit_events: Mapped[list["AuditEventDB"]] = relationship(
        "AuditEventDB",
        back_populates="transaction",
    )

    __table_args__ = (
        Index(
            "ix_transactions_card_status",
            "card_id",
            "status",
        ),
        CheckConstraint(
            "authorized_amount >= 0",
            name="ck_transactions_authorized_amount_non_negative",
        ),
        CheckConstraint(
            "captured_amount >= 0",
            name="ck_transactions_captured_amount_non_negative",
        ),
        CheckConstraint(
            "settled_amount >= 0",
            name="ck_transactions_settled_amount_non_negative",
        ),
        CheckConstraint(
            "refunded_amount >= 0",
            name="ck_transactions_refunded_amount_non_negative",
        ),
        CheckConstraint(
            "captured_amount <= authorized_amount",
            name="ck_transactions_capture_within_authorization",
        ),
        CheckConstraint(
            "settled_amount <= captured_amount",
            name="ck_transactions_settlement_within_capture",
        ),
        CheckConstraint(
            "refunded_amount <= settled_amount",
            name="ck_transactions_refund_within_settlement",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_transactions_version_positive",
        ),
    )


# ============================================================================
# Transaction Event Persistence Model
# ============================================================================

class TransactionEventDB(Base):
    """Append-oriented persistence model for transaction lifecycle events."""

    __tablename__ = "transaction_events"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    transaction_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    status: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    metadata_json: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    transaction: Mapped["TransactionDB"] = relationship(
        "TransactionDB",
        back_populates="events",
    )

    __table_args__ = (
        CheckConstraint(
            "amount IS NULL OR amount >= 0",
            name="ck_transaction_events_amount_non_negative",
        ),
        Index(
            "ix_transaction_events_transaction_created",
            "transaction_id",
            "created_at",
        ),
    )


# ============================================================================
# Audit Event Persistence Model
# ============================================================================

class AuditEventDB(Base):
    """Persistence model for operational and payment audit events."""

    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    transaction_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("transactions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    correlation_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    metadata_json: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    transaction: Mapped[Optional["TransactionDB"]] = relationship(
        "TransactionDB",
        back_populates="audit_events",
    )

    __table_args__ = (
        Index(
            "ix_audit_events_transaction_created",
            "transaction_id",
            "created_at",
        ),
        Index(
            "ix_audit_events_correlation_created",
            "correlation_id",
            "created_at",
        ),
    )


# ============================================================================
# Idempotency Persistence Model
# ============================================================================

class IdempotencyRecordDB(Base):
    """
    Persistence model for completed idempotent requests.

    The unique key constraint protects against duplicate key records.
    Atomic claiming and coordination of concurrent business operations
    must also be implemented in the repository/service layer.
    """

    __tablename__ = "idempotency_records"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    idempotency_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    fingerprint: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    response_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "idempotency_key",
            name="uq_idempotency_records_key",
        ),
    )
