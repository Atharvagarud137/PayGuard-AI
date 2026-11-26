# PayGuard-AI scenario domain model

**Status date: 26 November 2026.** Day 3's typed schema layer, Day 5's versioned definition/run storage, Day 6's deterministic runner and Day 7's assertion registry/finalization are implemented. GitHub Actions run [#93](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/45749516234) passed all three jobs. Exact test counts were not available in the inspected CI API response. The Day 3 isolated schema run is historical evidence, not full-repository verification.

## Boundary

Scenario definitions are declarative data, not executable code. They contain a typed action enum, scalar parameters, ordered dependencies and typed assertions. The schema rejects undeclared model fields, nested parameter values and parameter names commonly used for executable payloads (`script`, `command`, `cmd`, `executable`, `expression`, `eval`, `shell`). These restrictions are a schema boundary, not a substitute for future runner-side validation or security review.

The schema module itself does not execute actions or invoke payment APIs. Scenario persistence and basic execution are provided by separate storage and runner modules; failure injection and report generation remain future work.

## Definition schemas

- **ScenarioDefinition:** scenario ID, name, positive version, description, tags, creation timestamp, ordered steps and assertions.
- **ScenarioStepDefinition:** stable step ID, one of the declared actions, inert scalar parameters and dependencies on earlier steps.
- **ScenarioAssertionDefinition:** stable assertion ID, one of the declared assertion kinds, typed expected value and optional target step.

Actions currently represented in the schema are `authorize`, `capture`, `settle`, `refund`, `response_loss_after_commit`, `retry` and `verify`. Assertion kinds are `step_status`, `transaction_status`, `idempotency_replay`, `transaction_count`, `amount_invariant` and `audit_integrity`. These enum values are accepted action identifiers. The Day 6 runner dispatches only to handlers explicitly injected by its caller; the enum does not grant default implementations or permit arbitrary code.

## Run/result schemas

- **ScenarioRun:** UUID, scenario ID/version, status, creation/start/finish timestamps and optional failure reason.
- **ScenarioStepResult:** step ID, status, timing, scalar output and optional error.
- **ScenarioAssertionResult:** assertion ID, status, expected/observed values and optional message.
- **ScenarioRunResult:** scenario-version snapshot, run metadata, step results and assertion results.

The schemas validate lifecycle timestamp combinations, timezone-aware timestamps, identifier uniqueness/references, result IDs, expected-value consistency, and the completeness of a successful run. A failed run must include a failed step/assertion or a failure reason.

## Validation rules

- IDs use a restricted lowercase identifier format and are unique within a scenario/result set.
- Step dependencies must refer to earlier steps, preserving explicit ordering and preventing forward references/cycles in this representation.
- Assertion targets must refer to declared steps.
- Definitions and results reject undeclared fields.
- Parameter/output values are limited to scalar strings, integers, booleans or finite decimals; nested data and executable-oriented parameter keys are rejected.
- Monetary assertion values are non-negative finite decimals with at most two fractional places.
- Passed runs require every defined step and assertion to have a passing result.

## Day 6 runner skeleton\n\n`ScenarioRunner` receives an explicit action-to-handler mapping and an optional clock. It runs steps in their declared order, passes a copy of accumulated outputs to each handler, captures validated scalar outputs, sanitizes exceptions, marks dependent steps skipped after failures, and continues independent steps. A missing handler is a step failure. Results are returned in a `ScenarioRunResult` object and are not persisted by the runner.\n\nThe runner deliberately left run status `RUNNING` and assertion results empty through Day 6. Day 7 now evaluates assertions and finalizes runs. Run results and assertion observations remain in-memory only.\n\n## Remaining roadmap work\n\n

## Day 7 assertion evaluation and finalization (26 November 2026)

`AssertionRegistry` evaluates the six schema-defined assertion kinds deterministically:

- `step_status`: compares the target step's result status.
- `transaction_status`: reads the target step's `transaction_status` output (string values are normalized to the payment status enum).
- `idempotency_replay`: reads the `idempotency_replay` boolean output.
- `transaction_count`: reads the `transaction_count` integer output.
- `amount_invariant`: reads the `amount_invariant` Decimal output.
- `audit_integrity`: reads the `audit_integrity` boolean output.

For non-status assertions, an explicit target step restricts the observation source. Without a target, the latest step in declared scenario order containing the observation key is used. Missing or type-invalid observations fail rather than silently pass. Messages are generic and do not include arbitrary handler values.

Assertions are evaluated after step execution. The run is finalized as `PASSED` only when all defined steps and assertions pass; otherwise it is `FAILED` with a generic failure reason. Assertion results and step outputs are not persisted yet. CI run [#93](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/45749516234) passed all three jobs.

**Limits:** observations come from caller-injected handlers, not live payment/database/audit queries. No default action handlers, persisted evidence, report export or replay are added here. No local suite was executed because this environment lacks an executable checkout/terminal.
