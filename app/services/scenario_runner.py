"""Deterministic, injectable orchestration skeleton for scenario steps.
No action has default side effects; handlers are supplied by callers.
"""
from datetime import datetime, timezone
from typing import Callable

from app.domain.scenarios import ScenarioDefinition, ScenarioRun, ScenarioRunResult, ScenarioRunStatus, ScenarioStepResult, ScenarioStepStatus

StepHandler = Callable[[dict, dict[str, dict]], dict]


class ScenarioRunner:
    """Run declared steps in definition order using explicitly injected handlers."""

    def __init__(self, handlers: dict, *, clock: Callable = lambda: datetime.now(timezone.utc)):
        self.handlers = dict(handlers)
        self.clock = clock

    def run(self, scenario: ScenarioDefinition) -> ScenarioRunResult:
        run = ScenarioRun(scenario_id=scenario.scenario_id, scenario_version=scenario.version,
                          status=ScenarioRunStatus.RUNNING, started_at=self.clock())
        results = []
        outputs: dict[str, dict] = {}
        failed_ids: set[str] = {}

        for step in scenario.steps:
            if any(dependency in failed_ids for dependency in step.depends_on):
                results.append(ScenarioStepResult(step_id=step.step_id, status=ScenarioStepStatus.SKIPPED))
                failed_ids.add(step.step_id)
                continue
            handler = self.handlers.get(step.action)
            if handler is None:
                now = self.clock()
                results.append(ScenarioStepResult(step_id=step.step_id, status=ScenarioStepStatus.FAILED,
                    started_at=now, finished_at=self.clock(),
                    error=f"No handler registered for action '{step.action.value}'"))
                failed_ids.add(step.step_id)
                continue
            started = self.clock()
            try:
                output = handler(dict(step.parameters), dict(outputs))
                if not isinstance(output, dict):
                    raise TypeError("step handler must return a scalar-output dictionary")
                result = ScenarioStepResult(step_id=step.step_id, status=ScenarioStepStatus.PASSED,
                    started_at=started, finished_at=self.clock(), output=output)
                outputs[step.step_id] = dict(result.output)
            except Exception as exc:
                result = ScenarioStepResult(step_id=step.step_id, status=ScenarioStepStatus.FAILED,
                    started_at=started, finished_at=self.clock(),
                    error=f"{type(exc).__name__}: step handler failed")
                failed_ids.add(step.step_id)
            results.append(result)
        # Day 7 owns assertions/finalization. Never claim a run passed without them.
        return ScenarioRunResult(scenario=scenario, run=run, step_results=results)
