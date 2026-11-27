"""Persist scenario step/assertion evidence and ordered run timelines.

Revision ID: 007_scenario_evidence
Revises: 006_scenario_storage
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "007_scenario_evidence"
down_revision: Union[str, Sequence[str], None] = "006_scenario_storage"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scenario_step_evidence",
        sa.Column("run_id", sa.String(36), nullable=False),
        sa.Column("step_id", sa.String(64), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("output_json", postgresql.JSONB(), nullable=False),
        sa.Column("error", sa.String(1000), nullable=True),
        sa.PrimaryKeyConstraint("run_id", "step_id", name="pk_scenario_step_evidence"),
        sa.UniqueConstraint("run_id", "ordinal", name="uq_scenario_step_evidence_ordinal"),
        sa.ForeignKeyConstraint(["run_id"], ["scenario_runs.run_id"], name="fk_scenario_step_evidence_run", ondelete="RESTRICT"),
        sa.CheckConstraint("ordinal >= 1", name="ck_scenario_step_evidence_ordinal_positive"),
        sa.CheckConstraint("status IN ('pending', 'running', 'passed', 'failed', 'skipped')", name="ck_scenario_step_evidence_status"),
    )
    op.create_table(
        "scenario_assertion_evidence",
        sa.Column("run_id", sa.String(36), nullable=False),
        sa.Column("assertion_id", sa.String(64), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("expected_json", postgresql.JSONB(), nullable=False),
        sa.Column("observed_json", postgresql.JSONB(), nullable=True),
        sa.Column("message", sa.String(1000), nullable=True),
        sa.PrimaryKeyConstraint("run_id", "assertion_id", name="pk_scenario_assertion_evidence"),
        sa.UniqueConstraint("run_id", "ordinal", name="uq_scenario_assertion_evidence_ordinal"),
        sa.ForeignKeyConstraint(["run_id"], ["scenario_runs.run_id"], name="fk_scenario_assertion_evidence_run", ondelete="RESTRICT"),
        sa.CheckConstraint("ordinal >= 1", name="ck_scenario_assertion_evidence_ordinal_positive"),
        sa.CheckConstraint("status IN ('pending', 'passed', 'failed', 'skipped')", name="ck_scenario_assertion_evidence_status"),
    )
    op.create_table(
        "scenario_run_events",
        sa.Column("run_id", sa.String(36), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("step_id", sa.String(64), nullable=True),
        sa.Column("assertion_id", sa.String(64), nullable=True),
        sa.Column("payload_json", postgresql.JSONB(), nullable=False),
        sa.PrimaryKeyConstraint("run_id", "sequence", name="pk_scenario_run_events"),
        sa.ForeignKeyConstraint(["run_id"], ["scenario_runs.run_id"], name="fk_scenario_run_events_run", ondelete="RESTRICT"),
        sa.CheckConstraint("sequence >= 1", name="ck_scenario_run_events_sequence_positive"),
        sa.CheckConstraint("event_type IN ('run_started', 'step_started', 'step_completed', 'step_failed', 'step_skipped', 'assertion_evaluated', 'run_completed')", name="ck_scenario_run_events_type"),
    )
    op.create_index("ix_scenario_run_events_run_sequence", "scenario_run_events", ["run_id", "sequence"])
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'payguard_app') THEN
                REVOKE ALL PRIVILEGES ON TABLE public.scenario_step_evidence FROM payguard_app, PUBLIC;
                REVOKE ALL PRIVILEGES ON TABLE public.scenario_assertion_evidence FROM payguard_app, PUBLIC;
                REVOKE ALL PRIVILEGES ON TABLE public.scenario_run_events FROM payguard_app, PUBLIC;
                GRANT SELECT, INSERT ON TABLE public.scenario_step_evidence TO payguard_app;
                GRANT SELECT, INSERT ON TABLE public.scenario_assertion_evidence TO payguard_app;
                GRANT SELECT, INSERT ON TABLE public.scenario_run_events TO payguard_app;
            END IF;
        END
        $$;
    """)


def downgrade() -> None:
    op.drop_index("ix_scenario_run_events_run_sequence", table_name="scenario_run_events")
    op.drop_table("scenario_run_events")
    op.drop_table("scenario_assertion_evidence")
    op.drop_table("scenario_step_evidence")
