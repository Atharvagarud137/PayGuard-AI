"""Keep audit references independent of mutable payment-row lifecycle.

Revision ID: 005_audit_reference_without_fk
Revises: 004_audit_no_delete_exception
"""

from typing import Sequence, Union

from alembic import op


revision: str = "005_audit_reference_without_fk"
down_revision: Union[str, Sequence[str], None] = "004_audit_no_delete_exception"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Audit events are historical records. A foreign-key ON DELETE SET NULL
    # action would mutate an audit row when a synthetic transaction is reset,
    # violating append-only semantics and erasing useful historical context.
    op.drop_constraint(
        "fk_audit_events_transaction_id_transactions",
        "audit_events",
        type_="foreignkey",
    )


def downgrade() -> None:
    # Do not recreate the FK: existing audit references may intentionally
    # point to deleted synthetic transactions, and restoring SET NULL would
    # require mutating immutable audit history.
    pass
