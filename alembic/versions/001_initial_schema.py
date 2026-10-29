
"""Create the initial PayGuard-AI PostgreSQL schema.

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-09-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the initial PayGuard-AI persistence schema."""

    op.create_table(
        "cards",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("card_number", sa.String(length=19), nullable=False),
        sa.Column("cardholder_name", sa.String(length=255), nullable=False),
        sa.Column("network", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column(
            "balance",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
        ),
        sa.Column("expiry_date", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "card_number",
            name="uq_cards_card_number",
        ),
        sa.CheckConstraint(
            "balance >= 0",
            name="ck_cards_balance_non_negative",
        ),
    )

    op.create_index(
        "ix_cards_card_number",
        "cards",
        ["card_number"],
        unique=False,
    )
    op.create_index(
        "ix_cards_status",
        "cards",
        ["status"],
        unique=False,
    )

    op.create_table(
        "transactions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("card_id", sa.String(length=36), nullable=False),
        sa.Column("merchant_id", sa.String(length=255), nullable=True),
        sa.Column(
            "authorized_amount",
            sa.Numeric(precision=12, scale=2),
            server_default=sa.text("0.00"),
            nullable=False,
        ),
        sa.Column(
            "captured_amount",
            sa.Numeric(precision=12, scale=2),
            server_default=sa.text("0.00"),
            nullable=False,
        ),
        sa.Column(
            "settled_amount",
            sa.Numeric(precision=12, scale=2),
            server_default=sa.text("0.00"),
            nullable=False,
        ),
        sa.Column(
            "refunded_amount",
            sa.Numeric(precision=12, scale=2),
            server_default=sa.text("0.00"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("decline_reason", sa.Text(), nullable=True),
        sa.Column(
            "version",
            sa.Integer(),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["card_id"],
            ["cards.id"],
            name="fk_transactions_card_id_cards",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "authorized_amount >= 0",
            name="ck_transactions_authorized_amount_non_negative",
        ),
        sa.CheckConstraint(
            "captured_amount >= 0",
            name="ck_transactions_captured_amount_non_negative",
        ),
        sa.CheckConstraint(
            "settled_amount >= 0",
            name="ck_transactions_settled_amount_non_negative",
        ),
        sa.CheckConstraint(
            "refunded_amount >= 0",
            name="ck_transactions_refunded_amount_non_negative",
        ),
        sa.CheckConstraint(
            "captured_amount <= authorized_amount",
            name="ck_transactions_capture_not_exceed_authorization",
        ),
        sa.CheckConstraint(
            "settled_amount <= captured_amount",
            name="ck_transactions_settlement_not_exceed_capture",
        ),
        sa.CheckConstraint(
            "refunded_amount <= settled_amount",
            name="ck_transactions_refund_not_exceed_settlement",
        ),
        sa.CheckConstraint(
            "version >= 1",
            name="ck_transactions_version_positive",
        ),
    )

    op.create_index(
        "ix_transactions_card_id",
        "transactions",
        ["card_id"],
        unique=False,
    )
    op.create_index(
        "ix_transactions_merchant_id",
        "transactions",
        ["merchant_id"],
        unique=False,
    )
    op.create_index(
        "ix_transactions_status",
        "transactions",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_transactions_card_status",
        "transactions",
        ["card_id", "status"],
        unique=False,
    )

    op.create_table(
        "transaction_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("transaction_id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column(
            "amount",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["transaction_id"],
            ["transactions.id"],
            name="fk_transaction_events_transaction_id_transactions",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "amount IS NULL OR amount >= 0",
            name="ck_transaction_events_amount_non_negative",
        ),
    )

    op.create_index(
        "ix_transaction_events_transaction_id",
        "transaction_events",
        ["transaction_id"],
        unique=False,
    )
    op.create_index(
        "ix_transaction_events_event_type",
        "transaction_events",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        "ix_transaction_events_transaction_created",
        "transaction_events",
        ["transaction_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("transaction_id", sa.String(length=36), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("correlation_id", sa.String(length=255), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["transaction_id"],
            ["transactions.id"],
            name="fk_audit_events_transaction_id_transactions",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_audit_events_transaction_id",
        "audit_events",
        ["transaction_id"],
        unique=False,
    )
    op.create_index(
        "ix_audit_events_event_type",
        "audit_events",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        "ix_audit_events_correlation_id",
        "audit_events",
        ["correlation_id"],
        unique=False,
    )
    op.create_index(
        "ix_audit_events_created_at",
        "audit_events",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_audit_events_transaction_created",
        "audit_events",
        ["transaction_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_audit_events_correlation_created",
        "audit_events",
        ["correlation_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "idempotency_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "idempotency_key",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("response_json", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "idempotency_key",
            name="uq_idempotency_records_key",
        ),
    )

    op.create_index(
        "ix_idempotency_records_created_at",
        "idempotency_records",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Drop the initial PayGuard-AI persistence schema."""

    op.drop_index(
        "ix_idempotency_records_created_at",
        table_name="idempotency_records",
    )
    op.drop_table("idempotency_records")

    op.drop_index(
        "ix_audit_events_correlation_created",
        table_name="audit_events",
    )
    op.drop_index(
        "ix_audit_events_transaction_created",
        table_name="audit_events",
    )
    op.drop_index(
        "ix_audit_events_created_at",
        table_name="audit_events",
    )
    op.drop_index(
        "ix_audit_events_correlation_id",
        table_name="audit_events",
    )
    op.drop_index(
        "ix_audit_events_event_type",
        table_name="audit_events",
    )
    op.drop_index(
        "ix_audit_events_transaction_id",
        table_name="audit_events",
    )
    op.drop_table("audit_events")

    op.drop_index(
        "ix_transaction_events_transaction_created",
        table_name="transaction_events",
    )
    op.drop_index(
        "ix_transaction_events_event_type",
        table_name="transaction_events",
    )
    op.drop_index(
        "ix_transaction_events_transaction_id",
        table_name="transaction_events",
    )
    op.drop_table("transaction_events")

    op.drop_index(
        "ix_transactions_card_status",
        table_name="transactions",
    )
    op.drop_index(
        "ix_transactions_status",
        table_name="transactions",
    )
    op.drop_index(
        "ix_transactions_merchant_id",
        table_name="transactions",
    )
    op.drop_index(
        "ix_transactions_card_id",
        table_name="transactions",
    )
    op.drop_table("transactions")

    op.drop_index(
        "ix_cards_status",
        table_name="cards",
    )
    op.drop_index(
        "ix_cards_card_number",
        table_name="cards",
    )
    op.drop_table("cards")
