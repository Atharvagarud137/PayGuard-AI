from datetime import datetime, timezone
from decimal import Decimal

from app.domain.scenarios import (
    ScenarioAction, ScenarioAssertionDefinition, ScenarioAssertionKind,
    ScenarioDefinition, ScenarioStepDefinition, ScenarioRunRecord,
)
from app.repositories.postgres_scenario_repository import payload_sha256, scenario_payload
from app.services.scenario_report import build_scenario_run_report
from app.services.scenario_runner import ScenarioRunner

NOW = datetime(2026, 11, 28, 3, 30, tzinfo=timezone.utc)


def definition():
    return ScenarioDefinition(
        scenario_id="report-scenario", name="Synthetic report scenario", version=1,
        tags=["synthetic"],
        steps=[ScenarioStepDefinition(step_id="observe", action=ScenarioAction.VERIFY)],
        assertions=[
            ScenarioAssertionDefinition(assertion_id="count", kind=ScenarioAssertionKind.TRANSACTION_COUNT, expected=1),
            ScenarioAssertionDefinition(assertion_id="amount", kind=ScenarioAssertionKind.AMOUNT_INVARIANT, expected=Decimal("10.00")),
        ],
        created_at=NOW,
    )


def build_record(result, scenario):
    payload = scenario_payload(scenario)
    return ScenarioRunRecord(
        scenario=scenario, run=result.run, schema_version=1,
        snapshot_sha256=payload_sha256(payload),
    )


def test_report_summary_and_schema_version_for_passed_run():
    scenario = definition()
    result = ScenarioRunner(
        {ScenarioAction.VERIFY: lambda p, o: {"transaction_count": 1, "amount_invariant": Decimal("10.00")}},
        clock=lambda: NOW,
    ).run(scenario)
    report = build_scenario_run_report(build_record(result, scenario), result, generated_at=NOW)
    assert report.report_schema_version == 1
    assert report.summary.status.value == "passed"
    assert report.summary.total_steps == report.summary.passed_steps == 1
    assert report.summary.failed_steps == report.summary.skipped_steps == 0
    assert report.summary.total_assertions == report.summary.passed_assertions == 2
    assert report.summary.failed_assertions == report.summary.skipped_assertions == 0
    assert report.snapshot_sha256 == payload_sha256(scenario_payload(scenario))
    assert report.generated_at == NOW


def test_report_counts_failed_step_and_assertions_without_exposing_handler_exception():
    scenario = definition()

    def unsafe_handler(parameters, outputs):
        raise RuntimeError("synthetic handler failure with details that must not escape")

    result = ScenarioRunner({ScenarioAction.VERIFY: unsafe_handler}, clock=lambda: NOW).run(scenario)
    report = build_scenario_run_report(build_record(result, scenario), result, generated_at=NOW)
    assert report.summary.status.value == "failed"
    assert report.summary.failed_steps == 1
    assert report.summary.passed_steps == 0
    assert report.summary.failed_assertions == 2
    assert "details that must not escape" not in str(report.model_dump(mode="json"))
