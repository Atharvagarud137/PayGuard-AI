"""Remove the caller-settable audit deletion exception.

Revision ID: 004_audit_no_delete_exception
Revises: 003_audit_truncate_guard
"""

from typing import Sequence, Union

from alembic import op


revision: str = "004_audit_no_delete_exception"
down_revision: Union[str, Sequence[str], None] = "003_audit_truncate_guard"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # A custom PostgreSQL GUC can be set by any session using the application
    # credential. It must never be treated as an authorization boundary.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION payguard_prevent_audit_mutation()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION 'audit_events are append-only'
                USING ERRCODE = '55000';
        END;
        $$;
        """
    )


def downgrade() -> None:
    # Keep the stricter function on downgrade. Reintroducing a caller-controlled
    # deletion bypass would weaken the audit boundary.
    pass
