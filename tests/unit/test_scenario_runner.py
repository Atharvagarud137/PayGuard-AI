from datetime import datetime, timezone
from decimal import Decimal

from app.domain.scenarios import ScenarioAction, ScenarioAssertionKind, ScenarioAssertionDefinition, ScenarioDefinition, ScenarioStepDefinition, ScenarioStepStatus
from app.services.scenario_runner import ScenarioRunner

NOW = datetime(2026, 11, 25, 9, 0, tzinfo=timezone.utc)

def scenario(steps):
    return ScenarioDefinition(scenario_id="runner-sample", name="Runner sample", steps=steps,
        assertions=[ScenarioAssertionDefinition(assertion_id="count", kind=ScenarioAssertionKind.TRANSACTION_COUNT, expected=1)])

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
    assert result.run.status.value=="running"

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

def test_running_status_not_false_pass():
    result=ScenarioRunner({ScenarioAction.VERIFY:lambda p,o:{}},clock=lambda:NOW).run(
        scenario([ScenarioStepDefinition(step_id="first",action=ScenarioAction.VERIFY)]))
    assert result.run.started_at==NOW
    assert result.run.status.value=="running"
    assert result.assertion_results==[]
