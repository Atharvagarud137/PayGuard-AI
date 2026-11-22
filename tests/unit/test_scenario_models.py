from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.domain.scenarios import (
    ScenarioAction,
    ScenarioAssertionDefinition,
    ScenarioAssertionKind,
    ScenarioAssertionResult,
    ScenarioAssertionStatus,
    ScenarioDefinition,
    ScenarioRun,
    ScenarioRunResult,
    ScenarioRunStatus,
    ScenarioStepDefinition,
    ScenarioStepResult,
    ScenarioStepStatus,
)
from app.models import TransactionStatus


NOW = datetime(2026, 11, 22, 8, 0, tzinfo=timezone.utc)


def sample_scenario():
    return ScenarioDefinition(
        scenario_id="response-loss-retry",
        name="Response loss after commit and retry",
        version=1,
        tags=["idempotency", "failure-injection"],
        steps=[
            ScenarioStepDefinition(
                step_id="authorize",
                action=ScenarioAction.AUTHORIZE,
                parameters={"amount": Decimal("10.00"), "merchant_id": "synthetic-merchant"},
            ),
            ScenarioStepDefinition(
                step_id="inject-loss",
                action=ScenarioAction.RESPONSE_LOSS_AFTER_COMMIT,
                depends_on=["authorize"],
            ),
            ScenarioStepDefinition(
                step_id="retry",
                action=ScenarioAction.RETRY,
                parameters={"same_key": True},
                depends_on=["inject-loss"],
            ),
        ],
        assertions=[
            ScenarioAssertionDefinition(
                assertion_id="replayed",
                kind=ScenarioAssertionKind.IDEMPOTENCY_REPLAY,
                target_step_id="retry",
                expected=True,
            ),
            ScenarioAssertionDefinition(
                assertion_id="one-operation",
                kind=ScenarioAssertionKind.TRANSACTION_COUNT,
                expected=1,
            ),
            ScenarioAssertionDefinition(
                assertion_id="status",
                kind=ScenarioAssertionKind.TRANSACTION_STATUS,
                target_step_id="authorize",
                expected=TransactionStatus.AUTHORIZED,
            ),
        ],
        created_at=NOW,
    )


def test_scenario_definition_is_typed_and_declarative():
    scenario = sample_scenario()
    assert scenario.scenario_id == "response-loss-retry"
    assert scenario.steps[0].action == ScenarioAction.AUTHORIZE
    assert scenario.steps[2].depends_on == ["inject-loss"]
    assert scenario.assertions[0].expected is True
    assert scenario.assertions[2].expected == TransactionStatus.AUTHORIZED
    assert scenario.model_dump(mode="json")["scenario_id"] == scenario.scenario_id


def test_duplicate_step_ids_are_rejected():
    base = sample_scenario()
    duplicate_steps = [base.steps[0], base.steps[0]]
    with pytest.raises(ValidationError, match="step IDs must be unique"):
        ScenarioDefinition(
            scenario_id=base.scenario_id,
            name=base.name,
            steps=duplicate_steps,
            assertions=base.assertions,
        )


def test_step_cannot_depend_on_a_later_or_unknown_step():
    with pytest.raises(ValidationError, match="earlier steps"):
        ScenarioDefinition(
            scenario_id="invalid-order",
            name="Invalid dependency order",
            steps=[
                ScenarioStepDefinition(step_id="first", action=ScenarioAction.RETRY, depends_on=["later"]),
                ScenarioStepDefinition(step_id="later", action=ScenarioAction.VERIFY),
            ],
            assertions=[
                ScenarioAssertionDefinition(assertion_id="count", kind=ScenarioAssertionKind.TRANSACTION_COUNT, expected=1)
            ],
        )


def test_duplicate_dependencies_are_rejected():
    with pytest.raises(ValidationError, match="duplicates"):
        ScenarioStepDefinition(step_id="retry", action=ScenarioAction.RETRY, depends_on=["first", "first"])


def test_assertion_target_must_reference_defined_step():
    base = sample_scenario()
    invalid = ScenarioAssertionDefinition(
        assertion_id="missing-target",
        kind=ScenarioAssertionKind.STEP_STATUS,
        target_step_id="unknown",
        expected=ScenarioStepStatus.PASSED,
    )
    with pytest.raises(ValidationError, match="reference a scenario step"):
        ScenarioDefinition(
            scenario_id=base.scenario_id,
            name=base.name,
            steps=base.steps,
            assertions=[invalid],
        )


def test_assertion_expected_types_are_enforced():
    with pytest.raises(ValidationError, match="invalid type/value"):
        ScenarioAssertionDefinition(
            assertion_id="count",
            kind=ScenarioAssertionKind.TRANSACTION_COUNT,
            expected=True,
        )
    with pytest.raises(ValidationError):
        ScenarioAssertionDefinition(
            assertion_id="status",
            kind=ScenarioAssertionKind.TRANSACTION_STATUS,
            target_step_id="authorize",
            expected="not-a-payment-status",
        )


def test_scenario_rejects_blank_name_and_duplicate_tags():
    base = sample_scenario()
    with pytest.raises(ValidationError):
        ScenarioDefinition(scenario_id="blank", name=" ", steps=base.steps, assertions=base.assertions)
    with pytest.raises(ValidationError, match="duplicates"):
        ScenarioDefinition(scenario_id="tagged", name="Tagged", tags=["same", "same"], steps=base.steps, assertions=base.assertions)


@pytest.mark.parametrize("payload", [{"script": "anything"}, {"command": "anything"}, {"nested": {"code": "anything"}}, {"array": [1, 2]}])
def test_step_parameters_reject_executable_or_nested_payloads(payload):
    with pytest.raises(ValidationError):
        ScenarioStepDefinition(step_id="unsafe", action=ScenarioAction.VERIFY, parameters=payload)


def test_step_parameters_reject_non_finite_decimal():
    with pytest.raises(ValidationError):
        ScenarioStepDefinition(step_id="bad", action=ScenarioAction.VERIFY, parameters={"amount": Decimal("NaN")})


def test_run_lifecycle_schema():
    pending = ScenarioRun(scenario_id="sample", scenario_version=1, status=ScenarioRunStatus.PENDING)
    assert pending.started_at is None
    running = ScenarioRun(scenario_id="sample", scenario_version=1, status=ScenarioRunStatus.RUNNING, started_at=NOW)
    assert running.started_at == NOW
    with pytest.raises(ValidationError, match="terminal runs require"):
        ScenarioRun(scenario_id="sample", scenario_version=1, status=ScenarioRunStatus.PASSED, started_at=NOW)
    with pytest.raises(ValidationError, match="finished_at must not precede"):
        ScenarioRun(scenario_id="sample", scenario_version=1, status=ScenarioRunStatus.FAILED, started_at=NOW, finished_at=NOW - timedelta(seconds=1))
    with pytest.raises(ValidationError, match="timezone-aware"):
        ScenarioRun(scenario_id="sample", scenario_version=1, created_at=datetime(2026, 11, 22))


def test_step_result_status_and_failure_reason_rules():
    passed = ScenarioStepResult(step_id="authorize", status=ScenarioStepStatus.PASSED, started_at=NOW, finished_at=NOW + timedelta(seconds=1))
    assert passed.status == ScenarioStepStatus.PASSED
    with pytest.raises(ValidationError, match="require an error"):
        ScenarioStepResult(step_id="authorize", status=ScenarioStepStatus.FAILED, started_at=NOW, finished_at=NOW + timedelta(seconds=1))
    with pytest.raises(ValidationError, match="must not have timestamps"):
        ScenarioStepResult(step_id="authorize", status=ScenarioStepStatus.SKIPPED, started_at=NOW)


def test_passed_run_result_requires_all_defined_results_and_passes():
    scenario = sample_scenario()
    run = ScenarioRun(scenario_id=scenario.scenario_id, scenario_version=scenario.version, status=ScenarioRunStatus.PASSED, started_at=NOW, finished_at=NOW + timedelta(seconds=4))
    steps = [
        ScenarioStepResult(step_id=step.step_id, status=ScenarioStepStatus.PASSED, started_at=NOW, finished_at=NOW + timedelta(seconds=1))
        for step in scenario.steps
    ]
    assertions = [
        ScenarioAssertionResult(assertion_id=assertion.assertion_id, status=ScenarioAssertionStatus.PASSED, expected=assertion.expected, observed=assertion.expected)
        for assertion in scenario.assertions
    ]
    report = ScenarioRunResult(scenario=scenario, run=run, step_results=steps, assertion_results=assertions)
    assert report.run.status == ScenarioRunStatus.PASSED
    assert len(report.step_results) == 3


def test_passed_run_result_rejects_missing_assertion_result():
    scenario = sample_scenario()
    run = ScenarioRun(scenario_id=scenario.scenario_id, scenario_version=scenario.version, status=ScenarioRunStatus.PASSED, started_at=NOW, finished_at=NOW + timedelta(seconds=4))
    steps = [
        ScenarioStepResult(step_id=step.step_id, status=ScenarioStepStatus.PASSED, started_at=NOW, finished_at=NOW + timedelta(seconds=1))
        for step in scenario.steps
    ]
    assertions = [
        ScenarioAssertionResult(assertion_id=assertion.assertion_id, status=ScenarioAssertionStatus.PASSED, expected=assertion.expected, observed=assertion.expected)
        for assertion in scenario.assertions[:-1]
    ]
    with pytest.raises(ValidationError, match="every defined assertion"):
        ScenarioRunResult(scenario=scenario, run=run, step_results=steps, assertion_results=assertions)


def test_failed_run_result_requires_failure_evidence():
    scenario = sample_scenario()
    run = ScenarioRun(scenario_id=scenario.scenario_id, scenario_version=scenario.version, status=ScenarioRunStatus.FAILED, started_at=NOW, finished_at=NOW + timedelta(seconds=4))
    with pytest.raises(ValidationError, match="failed runs require"):
        ScenarioRunResult(scenario=scenario, run=run)
    failed_run = ScenarioRun(scenario_id=scenario.scenario_id, scenario_version=scenario.version, status=ScenarioRunStatus.FAILED, started_at=NOW, finished_at=NOW + timedelta(seconds=4), failure_reason="runner failure")
    report = ScenarioRunResult(scenario=scenario, run=failed_run)
    assert report.run.failure_reason == "runner failure"


def test_run_result_rejects_mismatched_scenario_version():
    scenario = sample_scenario()
    run = ScenarioRun(scenario_id=scenario.scenario_id, scenario_version=2, status=ScenarioRunStatus.PENDING)
    with pytest.raises(ValidationError, match="included scenario version"):
        ScenarioRunResult(scenario=scenario, run=run)


def test_run_result_rejects_unknown_result_ids_and_expected_value_drift():
    scenario = sample_scenario()
    run = ScenarioRun(scenario_id=scenario.scenario_id, scenario_version=scenario.version, status=ScenarioRunStatus.RUNNING, started_at=NOW)
    with pytest.raises(ValidationError, match="defined by the scenario"):
        ScenarioRunResult(scenario=scenario, run=run, step_results=[ScenarioStepResult(step_id="unknown", status=ScenarioStepStatus.PENDING)])
    changed_expected = ScenarioAssertionResult(assertion_id="replayed", status=ScenarioAssertionStatus.PENDING, expected=False)
    with pytest.raises(ValidationError, match="must match its definition"):
        ScenarioRunResult(scenario=scenario, run=run, assertion_results=[changed_expected])


def test_assertion_result_requires_observed_value_and_matching_type():
    with pytest.raises(ValidationError, match="observed value"):
        ScenarioAssertionResult(assertion_id="replayed", status=ScenarioAssertionStatus.PASSED, expected=True)
    with pytest.raises(ValidationError, match="same type"):
        ScenarioAssertionResult(assertion_id="replayed", status=ScenarioAssertionStatus.PASSED, expected=True, observed="true")