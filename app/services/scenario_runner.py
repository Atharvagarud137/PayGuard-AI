"""Deterministic scenario execution with assertion evaluation and finalization.

Handlers are explicitly injected. The runner never performs payment operations itself.
"""
from datetime import datetime, timezone
from typing import Callable

from app.domain.scenarios import (
    ScenarioAssertionDefinition,
    ScenarioAssertionKind,
    ScenarioAssertionResult,
    ScenarioAssertionStatus,
    ScenarioDefinition,
    ScenarioRun,
    ScenarioRunResult,
    ScenarioRunStatus,
    ScenarioStepResult,
    ScenarioStepStatus,
)
from app.models import TransactionStatus

StepHandler = Callable[[dict, dict[str, dict]], dict]


class AssertionRegistry:
    """Evaluate declared assertions against deterministic step-result observations.

    Non-step-status assertions read a scalar from a step output. If no target step
    is declared, the latest step (in scenario order) containing the observation
    key is used. Handler outputs are the observation boundary, not a live payment
    or database query.
    """

    _OUTPUT_KEYS = {
        ScenarioAssertionKind.TRANSACTION_STATUS: "transaction_status",
        ScenarioAssertionKind.IDEMPOTENCY_REPLAY: "idempotency_replay",
        ScenarioAssertionKind.TRANSACTION_COUNT: "transaction_count",
        ScenarioAssertionKind.AMOUNT_INVARIANT: "amount_invariant",
        ScenarioAssertionKind.AUDIT_INTEGRITY: "audit_integrity",
    }

    def evaluate(
        self, assertion: ScenarioAssertionDefinition, step_results: list[ScenarioStepResult]
    ) -> ScenarioAssertionResult:
        expected = assertion.expected
        observed = None
        message = None

        if assertion.kind == ScenarioAssertionKind.STEP_STATUS:
            target = next((r for r in step_results if r.step_id == assertion.target_step_id), None)
            if target is not None:
                observed = target.status
            else:
                message = "Target step result was not available"
        else:
            key = self._OUTPUT_KEYS[assertion.kind]
            candidates = step_results
            if assertion.target_step_id is not None:
                candidates = [r for r in step_results if r.step_id == assertion.target_step_id]
            source = next((r for r in reversed(candidates) if key in r.output), None)
            if source is None:
                message = f"No observation for '{key}'"
            else:
                observed = source.output[key]
                if assertion.kind == ScenarioAssertionKind.TRANSACTION_STATUS and type(observed) is str:
                    try:
                        observed = TransactionStatus(observed)
                    except ValueError:
                        observed = None
                        message = "Transaction-status observation has an invalid value"
                elif type(observed) is not type(expected):
                    observed = None
                    message = f"Observation for '{key}' has an invalid type"

        passed = observed is not None and type(observed) is type(expected) and observed == expected
        if passed:
            status = ScenarioAssertionStatus.PASSED
            message = None
        else:
            status = ScenarioAssertionStatus.FAILED
            message = message or "Observed value did not match the expected value"

        return ScenarioAssertionResult(
            assertion_id=assertion.assertion_id,
            status=status,
            expected=expected,
            observed=observed,
            message=message,
        )


class ScenarioRunner:
    """Run declared steps in order and evaluate assertions before finalizing."""

    def __init__(
        self,
        handlers: dict,
        *,
        clock: Callable = lambda: datetime.now(timezone.utc),
        assertion_registry: AssertionRegistry | None = None,
    ):
        self.handlers = dict(handlers)
        self.clock = clock
        self.assertion_registry = assertion_registry or AssertionRegistry()

    def run(self, scenario: ScenarioDefinition) -> ScenarioRunResult:
        run = ScenarioRun(
            scenario_id=scenario.scenario_id,
            scenario_version=scenario.version,
            status=ScenarioRunStatus.RUNNING,
            started_at=self.clock(),
        )
        results: list[ScenarioStepResult] = []
        outputs: dict[str, dict] = {}
        failed_ids: set[str] = set()

        for step in scenario.steps:
            if any(dependency in failed_ids for dependency in step.depends_on):
                results.append(
                    ScenarioStepResult(step_id=step.step_id, status=ScenarioStepStatus.SKIPPED)
                )
                failed_ids.add(step.step_id)
                continue

            handler = self.handlers.get(step.action)
            if handler is None:
                results.append(
                    ScenarioStepResult(
                        step_id=step.step_id,
                        status=ScenarioStepStatus.FAILED,
                        started_at=self.clock(),
                        finished_at=self.clock(),
                        error=f"No handler registered for action '{step.action.value}'",
                    )
                )
                failed_ids.add(step.step_id)
                continue

            started = self.clock()
            try:
                output = handler(dict(step.parameters), dict(outputs))
                if not isinstance(output, dict):
                    raise TypeError("step handler must return a scalar-output dictionary")
                result = ScenarioStepResult(
                    step_id=step.step_id,
                    status=ScenarioStepStatus.PASSED,
                    started_at=started,
                    finished_at=self.clock(),
                    output=output,
                )
                outputs[step.step_id] = dict(result.output)
            except Exception as exc:
                result = ScenarioStepResult(
                    step_id=step.step_id,
                    status=ScenarioStepStatus.FAILED,
                    started_at=started,
                    finished_at=self.clock(),
                    error=f"{type(exc).__name__}: step handler failed",
                )
                failed_ids.add(step.step_id)
            results.append(result)

        assertion_results = [
            self.assertion_registry.evaluate(assertion, results)
            for assertion in scenario.assertions
        ]
        all_steps_passed = len(results) == len(scenario.steps) and all(
            result.status == ScenarioStepStatus.PASSED for result in results
        )
        all_assertions_passed = len(assertion_results) == len(scenario.assertions) and all(
            result.status == ScenarioAssertionStatus.PASSED for result in assertion_results
        )
        passed = all_steps_passed and all_assertions_passed
        finished = self.clock()
        final_run = ScenarioRun(
            run_id=run.run_id,
            scenario_id=run.scenario_id,
            scenario_version=run.scenario_version,
            created_at=run.created_at,
            started_at=run.started_at,
            finished_at=finished,
            status=ScenarioRunStatus.PASSED if passed else ScenarioRunStatus.FAILED,
            failure_reason=None if passed else "One or more steps or assertions failed",
        )
        return ScenarioRunResult(
            scenario=scenario,
            run=final_run,
            step_results=results,
            assertion_results=assertion_results,
        )
