"""Persist immutable scenario versions and frozen run snapshots.

Revision ID: 006_scenario_storage
Revises: 005_audit_reference_without_fk
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "006_scenario_storage"
down_revision: Union[str, Sequence[str], None] = "005_audit_reference_without_fk"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scenario_definitions",
        sa.Column("scenario_id", sa.String(64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.JSONB(), nullable=False),
        sa.Column("definition_json", postgresql.JSONB(), nullable=False),
        sa.Column("definition_sha256", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("scenario_id", "version", name="pk_scenario_definitions"),
        sa.CheckConstraint("version >= 1", name="ck_scenario_definitions_version_positive"),
        sa.CheckConstraint("schema_version >= 1", name="ck_scenario_definitions_schema_version_positive"),
        sa.CheckConstraint("definition_sha256 ~ '^[0-9a-f]{64}$'",
                           name="ck_scenario_definitions_digest_format"),
    )
    op.create_table(
        "scenario_runs",
        sa.Column("run_id", sa.String(36), nullable=False),
        sa.Column("scenario_id", sa.String(64), nullable=False),
        sa.Column("scenario_version", sa.Integer(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.String(1000), nullable=True),
        sa.Column("snapshot_json", postgresql.JSONB(), nullable=False),
        sa.Column("snapshot_sha256", sa.String(64), nullable=False),
        sa.PrimaryKeyConstraint("run_id", name="pk_scenario_runs"),
        sa.ForeignKeyConstraint(
            ["scenario_id", "scenario_version"],
            ["scenario_definitions.scenario_id", "scenario_definitions.version"],
            name="fk_scenario_runs_definition_version", ondelete="RESTRICT",
        ),
        sa.CheckConstraint("scenario_version >= 1", name="ck_scenario_runs_scenario_version_positive"),
        sa.CheckConstraint("schema_version >= 1", name="ck_scenario_runs_schema_version_positive"),
        sa.CheckConstraint("status IN ('pending', 'running', 'passed', 'failed', 'cancelled')",
                           name="ck_scenario_runs_status"),
        sa.CheckConstraint(
            "(status = 'pending' AND started_at IS NULL AND finished_at IS NULL) OR "
            "(status = 'running' AND started_at IS NOT NULL AND finished_at IS NULL) OR "
            "(status IN ('passed', 'failed', 'cancelled') AND started_at IS NOT NULL "
            "AND finished_at IS NOT NULL AND finished_at >= started_at)",
            name="ck_scenario_runs_lifecycle",
        ),
        sa.CheckConstraint("status <> 'passed' OR failure_reason IS NULL",
                           name="ck_scenario_runs_passed_without_failure_reason"),
        sa.CheckConstraint("snapshot_sha256 ~ '^[0-9a-f]{64}$'",
                           name="ck_scenario_runs_snapshot_digest_format"),
    )
    op.create_index("ix_scenario_runs_scenario_version_created",
                    "scenario_runs", ["scenario_id", "scenario_version", "created_at"])
    op.create_index("ix_scenario_runs_status_created", "scenario_runs", ["status", "created_at"])

    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'payguard_app') THEN
                REVOKE UPDATE, DELETE, TRUNCATE ON TABLE public.scenario_definitions FROM payguard_app;
                REVOKE UPDATE, DELETE, TRUNCATE ON TABLE public.scenario_runs FROM payguard_app;
                GRANT SELECT, INSERT ON TABLE public.scenario_definitions TO payguard_app;
                GRANT SELECT, INSERT ON TABLE public.scenario_runs TO payguard_app;
                GRANT UPDATE (status, started_at, finished_at, failure_reason)
                    ON TABLE public.scenario_runs TO payguard_app;
            END IF;
        END
        $$;
    """)


def downgrade() -> None:
    op.drop_index("ix_scenario_runs_status_created", table_name="scenario_runs")
    op.drop_index("ix_scenario_runs_scenario_version_created", table_name="scenario_runs")
    op.drop_table("scenario_runs")
    op.drop_table("scenario_definitions")
