"""Prevent truncation of the append-only audit log.

Revision ID: 003_audit_truncate_guard
Revises: 002_audit_integrity
"""

from typing import Sequence, Union

from alembic import op


revision: str = "003_audit_truncate_guard"
down_revision: Union[str, Sequence[str], None] = "002_audit_integrity"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TRIGGER audit_events_prevent_truncate
        BEFORE TRUNCATE ON audit_events
        FOR EACH STATEMENT
        EXECUTE FUNCTION payguard_prevent_audit_mutation();
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS audit_events_prevent_truncate "
        "ON audit_events"
    )
