"""Versioned, machine-readable scenario-run reports built from persisted evidence."""

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

from app.domain.scenarios import (
    ScenarioAssertionResult,
    ScenarioAssertionStatus,
    ScenarioDefinition,
    ScenarioRun,
    ScenarioRunRecord,
    ScenarioRunResult,
    ScenarioRunStatus,
    ScenarioRunEvent,
    ScenarioStepResult,
    ScenarioStepStatus,
)


class ScenarioReportSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: ScenarioRunStatus
    total_steps: StrictInt = Field(ge=0)
    passed_steps: StrictInt = Field(ge=0)
    failed_steps: StrictInt = Field(ge=0)
    skipped_steps: StrictInt = Field(ge=0)
    total_assertions: StrictInt = Field(ge=0)
    passed_assertions: StrictInt = Field(ge=0)
    failed_assertions: StrictInt = Field(ge=0)
    skipped_assertions: StrictInt = Field(ge=0)
    duration_ms: StrictInt = Field(ge=0)


class ScenarioRunReportV1(BaseModel):
    """Public report contract. Add new incompatible shapes as a new version."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    report_schema_version: Literal[1] = 1
    generated_at: datetime
    scenario_storage_schema_version: StrictInt = Field(ge=1)
    snapshot_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    scenario: ScenarioDefinition
    run: ScenarioRun
    summary: ScenarioReportSummary
    step_results: list[ScenarioStepResult] = Field(max_length=50)
    assertion_results: list[ScenarioAssertionResult] = Field(max_length=100)
    timeline: list[ScenarioRunEvent] = Field(max_length=300)

    @model_validator(mode="after")
    def validate_report_consistency(self):
        if self.run.status not in {ScenarioRunStatus.PASSED, ScenarioRunStatus.FAILED}:
            raise ValueError("reports require a terminal passed or failed run")
        if self.summary.status != self.run.status:
            raise ValueError("report summary status must match the run")
        if self.run.scenario_id != self.scenario.scenario_id or self.run.scenario_version != self.scenario.version:
            raise ValueError("report run must reference the included scenario")
        if self.summary.total_steps != len(self.scenario.steps):
            raise ValueError("report step count must match the scenario")
        if self.summary.total_assertions != len(self.scenario.assertions):
            raise ValueError("report assertion count must match the scenario")
        return self


def build_scenario_run_report(
    record: ScenarioRunRecord,
    evidence: ScenarioRunResult,
    *,
    generated_at: datetime | None = None,
) -> ScenarioRunReportV1:
    """Create schema-v1 report data from a verified stored run and its evidence."""
    if record.run.run_id != evidence.run.run_id:
        raise ValueError("report evidence run ID does not match the stored run")
    if record.run.status != evidence.run.status or record.run.started_at != evidence.run.started_at or record.run.finished_at != evidence.run.finished_at:
        raise ValueError("report evidence lifecycle does not match the stored run")
    if record.scenario != evidence.scenario:
        raise ValueError("report evidence does not match the stored scenario snapshot")
    if evidence.run.status not in {ScenarioRunStatus.PASSED, ScenarioRunStatus.FAILED}:
        raise ValueError("only terminal scenario runs can be reported")
    if evidence.run.started_at is None or evidence.run.finished_at is None:
        raise ValueError("terminal run timestamps are required")

    duration_ms = max(0, int((evidence.run.finished_at - evidence.run.started_at).total_seconds() * 1000))
    summary = ScenarioReportSummary(
        status=evidence.run.status,
        total_steps=len(evidence.scenario.steps),
        passed_steps=sum(item.status == ScenarioStepStatus.PASSED for item in evidence.step_results),
        failed_steps=sum(item.status == ScenarioStepStatus.FAILED for item in evidence.step_results),
        skipped_steps=sum(item.status == ScenarioStepStatus.SKIPPED for item in evidence.step_results),
        total_assertions=len(evidence.scenario.assertions),
        passed_assertions=sum(item.status == ScenarioAssertionStatus.PASSED for item in evidence.assertion_results),
        failed_assertions=sum(item.status == ScenarioAssertionStatus.FAILED for item in evidence.assertion_results),
        skipped_assertions=sum(item.status == ScenarioAssertionStatus.SKIPPED for item in evidence.assertion_results),
        duration_ms=duration_ms,
    )
    return ScenarioRunReportV1(
        generated_at=generated_at or datetime.now(timezone.utc),
        scenario_storage_schema_version=record.schema_version,
        snapshot_sha256=record.snapshot_sha256,
        scenario=evidence.scenario,
        run=evidence.run,
        summary=summary,
        step_results=evidence.step_results,
        assertion_results=evidence.assertion_results,
        timeline=evidence.events,
    )
