"""Add append-only audit hash chain safeguards.

Revision ID: 002_audit_integrity
Revises: 001_initial_schema
"""

import hashlib
import json
from datetime import timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "002_audit_integrity"
down_revision: Union[str, Sequence[str], None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ZERO_HASH = "0" * 64


def _event_hash(previous_hash: str, sequence: int, row) -> str:
    created_at = row["created_at"]
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    created_at = created_at.astimezone(timezone.utc)

    payload = {
        "sequence": sequence,
        "id": row["id"],
        "transaction_id": row["transaction_id"],
        "event_type": row["event_type"],
        "message": row["message"],
        "correlation_id": row["correlation_id"],
        "metadata_json": row["metadata_json"] or {},
        "created_at": created_at.isoformat(),
    }
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )
    return hashlib.sha256(
        f"{previous_hash}:{canonical}".encode("utf-8")
    ).hexdigest()


def upgrade() -> None:
    op.add_column(
        "audit_events",
        sa.Column("chain_sequence", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "audit_events",
        sa.Column("previous_hash", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "audit_events",
        sa.Column("event_hash", sa.String(length=64), nullable=True),
    )

    connection = op.get_bind()
    rows = connection.execute(
        sa.text(
            "SELECT id, transaction_id, event_type, message, "
            "correlation_id, metadata_json, created_at "
            "FROM audit_events ORDER BY created_at ASC, id ASC"
        )
    ).mappings().all()

    previous_hash = _ZERO_HASH
    for sequence, row in enumerate(rows, start=1):
        digest = _event_hash(previous_hash, sequence, row)
        connection.execute(
            sa.text(
                "UPDATE audit_events SET chain_sequence=:sequence, "
                "previous_hash=:previous_hash, event_hash=:event_hash "
                "WHERE id=:event_id"
            ),
            {
                "sequence": sequence,
                "previous_hash": previous_hash,
                "event_hash": digest,
                "event_id": row["id"],
            },
        )
        previous_hash = digest

    op.alter_column(
        "audit_events",
        "chain_sequence",
        existing_type=sa.BigInteger(),
        nullable=False,
    )
    op.alter_column(
        "audit_events",
        "previous_hash",
        existing_type=sa.String(length=64),
        nullable=False,
    )
    op.alter_column(
        "audit_events",
        "event_hash",
        existing_type=sa.String(length=64),
        nullable=False,
    )
    op.create_unique_constraint(
        "uq_audit_events_chain_sequence",
        "audit_events",
        ["chain_sequence"],
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION payguard_prevent_audit_mutation()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            IF TG_OP = 'DELETE'
               AND current_setting(
                   'payguard.allow_audit_delete', true
               ) = 'on' THEN
                RETURN OLD;
            END IF;

            RAISE EXCEPTION 'audit_events are append-only'
                USING ERRCODE = '55000';
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_events_prevent_mutation
        BEFORE UPDATE OR DELETE ON audit_events
        FOR EACH ROW
        EXECUTE FUNCTION payguard_prevent_audit_mutation();
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS audit_events_prevent_mutation "
        "ON audit_events"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS payguard_prevent_audit_mutation()"
    )
    op.drop_constraint(
        "uq_audit_events_chain_sequence",
        "audit_events",
        type_="unique",
    )
    op.drop_column("audit_events", "event_hash")
    op.drop_column("audit_events", "previous_hash")
    op.drop_column("audit_events", "chain_sequence")
