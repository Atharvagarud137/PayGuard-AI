# PayGuard-AI scenario domain model

**Status date: 22 November 2026 (Day 3).** The typed schema layer and validation tests are implemented in this increment. GitHub Actions run [#80](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/44981213809) passed all three jobs: 163 Python/unit/API tests (1 warning), 6 E2E tests (2 warnings) and dependency audits. The separate temporary isolated schema run also passed 20 tests using a minimal `TransactionStatus` stub, but it was not full-repository verification. Scenario persistence and execution are not implemented.

## Boundary

Scenario definitions are declarative data, not executable code. They contain a typed action enum, scalar parameters, ordered dependencies and typed assertions. The schema rejects undeclared model fields, nested parameter values and parameter names commonly used for executable payloads (`script`, `command`, `cmd`, `executable`, `expression`, `eval`, `shell`). These restrictions are a schema boundary, not a substitute for future runner-side validation or security review.

The schema module does not execute actions, invoke payment APIs, persist scenarios, perform failure injection or produce reports from actual runs.

## Definition schemas

- **ScenarioDefinition:** scenario ID, name, positive version, description, tags, creation timestamp, ordered steps and assertions.
- **ScenarioStepDefinition:** stable step ID, one of the declared actions, inert scalar parameters and dependencies on earlier steps.
- **ScenarioAssertionDefinition:** stable assertion ID, one of the declared assertion kinds, typed expected value and optional target step.

Actions currently represented in the schema are `authorize`, `capture`, `settle`, `refund`, `response_loss_after_commit`, `retry` and `verify`. Assertion kinds are `step_status`, `transaction_status`, `idempotency_replay`, `transaction_count`, `amount_invariant` and `audit_integrity`. These enum values are contracts for future runner work; they are not yet executable capabilities.

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

## Not yet designed or implemented

The storage/migration decision, persistence lifecycle, action-specific parameter contracts, runner semantics, failure-injection controls, evidence retention and report export are subsequent roadmap work. Day 4 will document storage design before implementation. No real payment data or production credentials are permitted.