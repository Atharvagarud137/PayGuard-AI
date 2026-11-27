from datetime import datetime, timezone
from decimal import Decimal

from app.domain.scenarios import (ScenarioAction, ScenarioAssertionKind, ScenarioAssertionDefinition, ScenarioDefinition, ScenarioStepDefinition, ScenarioStepStatus, ScenarioAssertionStatus, ScenarioAssertionResult, ScenarioAssertionDefinition, ScenarioAssertionKind, ScenarioAssertionStatus, ScenarioStepStatus, TransactionStatus)
from app.services.scenario_runner import ScenarioRunner

NOW = datetime(2026, 11, 25, 9, 0, tzinfo=timezone.utc)

def scenario(steps):
    return ScenarioDefinition(scenario_id="runner-sample", name="Runner sample", steps=steps,
        assertions=[ScenarioAssertionDefinition(assertion_id="first-status", kind=ScenarioAssertionKind.STEP_STATUS,
            target_step_id=steps[0].step_id, expected=ScenarioStepStatus.PASSED)])

def test_order_and_context():
    seen=[]
    runner=ScenarioRunner({
        ScenarioAction.VERIFY: lambda p,o: (seen.append((p,o)) or {"value":1}),
        ScenarioAction.RETRY: lambda p,o: {"previous":o["first"]["value"]},
    }, clock=lambda:NOW)
    result=runner.run(scenario([
        ScenarioStepDefinition(step_id="first",action=ScenarioAction.VERIFY,parameters={"input":"x"}),
        ScenarioStepDefinition(step_id="second",action=ScenarioAction.RETRY,depends_on=["first"]),
    ]))
    assert [r.step_id for r in result.step_results]==["first","second"]
    assert all(r.status==ScenarioStepStatus.PASSED for r in result.step_results)
    assert result.step_results[1].output=={"previous":1}
    assert result.run.status.value=="passed"
    assert result.events[0].event_type.value=="run_started"
    assert result.events[-1].event_type.value=="run_completed"
    assert [event.sequence for event in result.events]==list(range(1,len(result.events)+1))

def test_missing_handler_fails_and_skips_dependency():
    result=ScenarioRunner({},clock=lambda:NOW).run(scenario([
        ScenarioStepDefinition(step_id="first",action=ScenarioAction.AUTHORIZE),
        ScenarioStepDefinition(step_id="second",action=ScenarioAction.CAPTURE,depends_on=["first"]),
    ]))
    assert result.step_results[0].status==ScenarioStepStatus.FAILED
    assert result.step_results[1].status==ScenarioStepStatus.SKIPPED

def test_failure_skips_dependents_but_independent_step_runs():
    called=[]
    result=ScenarioRunner({
        ScenarioAction.VERIFY:lambda p,o:(_ for _ in ()).throw(RuntimeError("sensitive detail")),
        ScenarioAction.SETTLE:lambda p,o:(called.append("independent") or {}),
    },clock=lambda:NOW).run(scenario([
        ScenarioStepDefinition(step_id="first",action=ScenarioAction.VERIFY),
        ScenarioStepDefinition(step_id="dependent",action=ScenarioAction.RETRY,depends_on=["first"]),
        ScenarioStepDefinition(step_id="independent",action=ScenarioAction.SETTLE),
    ]))
    assert result.step_results[0].status==ScenarioStepStatus.FAILED
    assert result.step_results[0].error=="RuntimeError: step handler failed"
    assert result.step_results[1].status==ScenarioStepStatus.SKIPPED
    assert result.step_results[2].status==ScenarioStepStatus.PASSED
    assert called==["independent"]

def test_invalid_nested_output_is_rejected_and_sanitized():
    result=ScenarioRunner({ScenarioAction.VERIFY:lambda p,o:{"nested":{"not":"scalar"}}},clock=lambda:NOW).run(
        scenario([ScenarioStepDefinition(step_id="first",action=ScenarioAction.VERIFY)]))
    assert result.step_results[0].status==ScenarioStepStatus.FAILED
    assert "not" not in result.step_results[0].error

def test_decimal_output_preserved():
    result=ScenarioRunner({ScenarioAction.VERIFY:lambda p,o:{"amount":Decimal("1.25")}},clock=lambda:NOW).run(
        scenario([ScenarioStepDefinition(step_id="first",action=ScenarioAction.VERIFY)]))
    assert result.step_results[0].output["amount"]==Decimal("1.25")

def test_runner_finalizes_passed_run_and_assertion():
    result=ScenarioRunner({ScenarioAction.VERIFY:lambda p,o:{}},clock=lambda:NOW).run(
        scenario([ScenarioStepDefinition(step_id="first",action=ScenarioAction.VERIFY)]))
    assert result.run.started_at==NOW
    assert result.run.finished_at==NOW
    assert result.run.status.value=="passed"
    assert result.assertion_results[0].status==ScenarioAssertionStatus.PASSED


def test_all_assertion_kinds_pass_and_finalize_run():
    assertions = [
        ScenarioAssertionDefinition(assertion_id="step-status", kind=ScenarioAssertionKind.STEP_STATUS,
            target_step_id="observe", expected=ScenarioStepStatus.PASSED),
        ScenarioAssertionDefinition(assertion_id="transaction-status", kind=ScenarioAssertionKind.TRANSACTION_STATUS,
            target_step_id="observe", expected=TransactionStatus.AUTHORIZED),
        ScenarioAssertionDefinition(assertion_id="replay", kind=ScenarioAssertionKind.IDEMPOTENCY_REPLAY,
            target_step_id="observe", expected=True),
        ScenarioAssertionDefinition(assertion_id="count", kind=ScenarioAssertionKind.TRANSACTION_COUNT,
            target_step_id="observe", expected=1),
        ScenarioAssertionDefinition(assertion_id="amount", kind=ScenarioAssertionKind.AMOUNT_INVARIANT,
            target_step_id="observe", expected=Decimal("10.00")),
        ScenarioAssertionDefinition(assertion_id="audit", kind=ScenarioAssertionKind.AUDIT_INTEGRITY,
            target_step_id="observe", expected=True),
    ]
    sample = ScenarioDefinition(scenario_id="assertions-pass", name="Assertion registry",
        steps=[ScenarioStepDefinition(step_id="observe", action=ScenarioAction.VERIFY)],
        assertions=assertions)
    handler = lambda p, o: {"transaction_status":"AUTHORIZED", "idempotency_replay":True,
        "transaction_count":1, "amount_invariant":Decimal("10.00"), "audit_integrity":True}
    result = ScenarioRunner({ScenarioAction.VERIFY:handler}, clock=lambda:NOW).run(sample)
    assert [r.status for r in result.assertion_results] == [ScenarioAssertionStatus.PASSED]*6
    assert result.run.status.value == "passed"
    assert result.run.finished_at == NOW


def test_assertion_mismatch_fails_run():
    assertion = ScenarioAssertionDefinition(assertion_id="count", kind=ScenarioAssertionKind.TRANSACTION_COUNT,
        target_step_id="observe", expected=2)
    sample = ScenarioDefinition(scenario_id="assertion-mismatch", name="Mismatch",
        steps=[ScenarioStepDefinition(step_id="observe", action=ScenarioAction.VERIFY)], assertions=[assertion])
    result = ScenarioRunner({ScenarioAction.VERIFY:lambda p,o:{"transaction_count":1}},clock=lambda:NOW).run(sample)
    assertion_result = result.assertion_results[0]
    assert assertion_result.status == ScenarioAssertionStatus.FAILED
    assert assertion_result.observed == 1
    assert assertion_result.message
    assert result.run.status.value == "failed"
    assert result.run.finished_at == NOW


def test_missing_observation_fails_assertion_without_observed_value():
    assertion = ScenarioAssertionDefinition(assertion_id="audit", kind=ScenarioAssertionKind.AUDIT_INTEGRITY,
        expected=True)
    sample = ScenarioDefinition(scenario_id="missing-observation", name="Missing",
        steps=[ScenarioStepDefinition(step_id="observe", action=ScenarioAction.VERIFY)], assertions=[assertion])
    result = ScenarioRunner({ScenarioAction.VERIFY:lambda p,o:{}},clock=lambda:NOW).run(sample)
    assertion_result = result.assertion_results[0]
    assert assertion_result.status == ScenarioAssertionStatus.FAILED
    assert assertion_result.observed is None
    assert "No observation" in assertion_result.message
    assert result.run.status.value == "failed"


def test_sensitive_output_keys_are_rejected_and_error_is_sanitized():
    result = ScenarioRunner({ScenarioAction.VERIFY:lambda p,o:{"cvv":"123"}},clock=lambda:NOW).run(
        scenario([ScenarioStepDefinition(step_id="first",action=ScenarioAction.VERIFY)]))
    assert result.step_results[0].status==ScenarioStepStatus.FAILED
    assert "123" not in result.step_results[0].error
    assert result.run.status.value=="failed"
