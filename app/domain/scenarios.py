"""Typed, inert definitions and result records for reliability scenarios.

This module intentionally contains no runner, command, script, or persistence code.
"""
from datetime import datetime, timezone
import re
from decimal import Decimal
from enum import Enum
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr, field_validator, model_validator

from app.models import TransactionStatus


_ID_PATTERN = r"^[a-z][a-z0-9_-]{0,63}$"
_BLOCKED_PARAMETER_NAMES = frozenset({"script", "command", "cmd", "executable", "expression", "eval", "shell"})
StrictDecimal = Annotated[Decimal, Field(strict=True)]
ScenarioScalar = StrictStr | StrictInt | StrictBool | StrictDecimal


def _aware(value: datetime | None, field_name: str) -> datetime | None:
    if value is not None and (value.tzinfo is None or value.utcoffset() is None):
        raise ValueError(f"{field_name} must be timezone-aware")
    return value


def _validate_scalars(values: dict[str, ScenarioScalar]) -> dict[str, ScenarioScalar]:
    for key, value in values.items():
        if not key.strip() or len(key) > 64:
            raise ValueError("parameter keys must be 1–64 non-whitespace characters")
        if key.strip().lower() in _BLOCKED_PARAMETER_NAMES:
            raise ValueError(f"parameter key '{key}' is not allowed")
        if isinstance(value, Decimal) and not value.is_finite():
            raise ValueError("decimal parameters must be finite")
    return values


class ScenarioModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ScenarioStepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ScenarioAssertionStatus(str, Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ScenarioRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScenarioAction(str, Enum):
    AUTHORIZE = "authorize"
    CAPTURE = "capture"
    SETTLE = "settle"
    REFUND = "refund"
    RESPONSE_LOSS_AFTER_COMMIT = "response_loss_after_commit"
    RETRY = "retry"
    VERIFY = "verify"


class ScenarioAssertionKind(str, Enum):
    STEP_STATUS = "step_status"
    TRANSACTION_STATUS = "transaction_status"
    IDEMPOTENCY_REPLAY = "idempotency_replay"
    TRANSACTION_COUNT = "transaction_count"
    AMOUNT_INVARIANT = "amount_invariant"
    AUDIT_INTEGRITY = "audit_integrity"


ScenarioExpected = ScenarioScalar | ScenarioStepStatus | TransactionStatus


class ScenarioStepDefinition(ScenarioModel):
    step_id: str = Field(pattern=_ID_PATTERN)
    action: ScenarioAction
    description: str | None = Field(default=None, max_length=500)
    parameters: dict[str, ScenarioScalar] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list, max_length=50)

    @field_validator("parameters")
    @classmethod
    def validate_parameters(cls, value: dict[str, ScenarioScalar]) -> dict[str, ScenarioScalar]:
        return _validate_scalars(value)

    @field_validator("depends_on")
    @classmethod
    def validate_dependencies(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("step dependencies must not contain duplicates")
        for dependency in value:
            if not re.fullmatch(_ID_PATTERN, dependency):
                raise ValueError("dependency identifiers must use the scenario ID format")
        return value


class ScenarioAssertionDefinition(ScenarioModel):
    assertion_id: str = Field(pattern=_ID_PATTERN)
    kind: ScenarioAssertionKind
    target_step_id: str | None = Field(default=None, pattern=_ID_PATTERN)
    expected: ScenarioExpected
    description: str | None = Field(default=None, max_length=500)

    @model_validator(mode="before")
    @classmethod
    def normalize_expected_enums(cls, value):
        if not isinstance(value, dict):
            return value
        normalized = dict(value)
        kind = normalized.get("kind")
        kind_value = kind.value if isinstance(kind, Enum) else kind
        expected = normalized.get("expected")
        if kind_value == ScenarioAssertionKind.STEP_STATUS.value and isinstance(expected, str):
            normalized["expected"] = ScenarioStepStatus(expected)
        elif kind_value == ScenarioAssertionKind.TRANSACTION_STATUS.value and isinstance(expected, str):
            normalized["expected"] = TransactionStatus(expected)
        return normalized

    @model_validator(mode="after")
    def validate_expected_type(self):
        expected = self.expected
        if self.kind == ScenarioAssertionKind.STEP_STATUS:
            valid = isinstance(expected, ScenarioStepStatus) and self.target_step_id is not None
        elif self.kind == ScenarioAssertionKind.TRANSACTION_STATUS:
            valid = isinstance(expected, TransactionStatus) and self.target_step_id is not None
        elif self.kind in {ScenarioAssertionKind.IDEMPOTENCY_REPLAY, ScenarioAssertionKind.AUDIT_INTEGRITY}:
            valid = type(expected) is bool
        elif self.kind == ScenarioAssertionKind.TRANSACTION_COUNT:
            valid = type(expected) is int and expected >= 0
        elif self.kind == ScenarioAssertionKind.AMOUNT_INVARIANT:
            valid = isinstance(expected, Decimal) and expected.is_finite() and expected >= 0 and expected.as_tuple().exponent >= -2
        else:
            valid = False
        if not valid:
            raise ValueError(f"expected value has an invalid type/value for assertion kind '{self.kind.value}'")
        return self


class ScenarioDefinition(ScenarioModel):
    scenario_id: str = Field(pattern=_ID_PATTERN)
    name: str = Field(min_length=1, max_length=120)
    version: int = Field(default=1, ge=1)
    description: str | None = Field(default=None, max_length=2000)
    tags: list[str] = Field(default_factory=list, max_length=20)
    steps: list[ScenarioStepDefinition] = Field(min_length=1, max_length=50)
    assertions: list[ScenarioAssertionDefinition] = Field(min_length=1, max_length=100)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("scenario name must not be blank")
        return value

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: list[str]) -> list[str]:
        normalized = [tag.strip() for tag in value]
        if any(not tag for tag in normalized):
            raise ValueError("tags must not be blank")
        if len(normalized) != len(set(normalized)):
            raise ValueError("tags must not contain duplicates")
        return normalized

    @field_validator("created_at")
    @classmethod
    def validate_created_at(cls, value: datetime) -> datetime:
        return _aware(value, "created_at")

    @model_validator(mode="after")
    def validate_references_and_order(self):
        seen_steps: set[str] = set()
        for step in self.steps:
            if step.step_id in seen_steps:
                raise ValueError("step IDs must be unique")
            unknown_or_later = set(step.depends_on) - seen_steps
            if unknown_or_later:
                raise ValueError("steps may only depend on earlier steps")
            seen_steps.add(step.step_id)

        seen_assertions: set[str] = set()
        for assertion in self.assertions:
            if assertion.assertion_id in seen_assertions:
                raise ValueError("assertion IDs must be unique")
            if assertion.target_step_id is not None and assertion.target_step_id not in seen_steps:
                raise ValueError("assertion target_step_id must reference a scenario step")
            seen_assertions.add(assertion.assertion_id)
        return self


class ScenarioRun(ScenarioModel):
    run_id: UUID = Field(default_factory=uuid4)
    scenario_id: str = Field(pattern=_ID_PATTERN)
    scenario_version: int = Field(ge=1)
    status: ScenarioRunStatus = ScenarioRunStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    finished_at: datetime | None = None
    failure_reason: str | None = Field(default=None, max_length=1000)

    @field_validator("created_at", "started_at", "finished_at")
    @classmethod
    def validate_timestamps(cls, value: datetime | None) -> datetime | None:
        return _aware(value, "run timestamp")

    @model_validator(mode="after")
    def validate_lifecycle(self):
        if self.status == ScenarioRunStatus.PENDING:
            if self.started_at is not None or self.finished_at is not None:
                raise ValueError("pending runs must not have start or finish timestamps")
        elif self.status == ScenarioRunStatus.RUNNING:
            if self.started_at is None or self.finished_at is not None:
                raise ValueError("running runs require started_at and must not have finished_at")
        else:
            if self.started_at is None or self.finished_at is None:
                raise ValueError("terminal runs require started_at and finished_at")
            if self.finished_at < self.started_at:
                raise ValueError("finished_at must not precede started_at")
        if self.status == ScenarioRunStatus.PASSED and self.failure_reason is not None:
            raise ValueError("passed runs must not have a failure_reason")
        return self


class ScenarioStepResult(ScenarioModel):
    step_id: str = Field(pattern=_ID_PATTERN)
    status: ScenarioStepStatus
    started_at: datetime | None = None
    finished_at: datetime | None = None
    output: dict[str, ScenarioScalar] = Field(default_factory=dict)
    error: str | None = Field(default=None, max_length=1000)

    @field_validator("started_at", "finished_at")
    @classmethod
    def validate_timestamps(cls, value: datetime | None) -> datetime | None:
        return _aware(value, "step timestamp")

    @field_validator("output")
    @classmethod
    def validate_output(cls, value: dict[str, ScenarioScalar]) -> dict[str, ScenarioScalar]:
        return _validate_scalars(value)

    @model_validator(mode="after")
    def validate_lifecycle(self):
        if self.status in {ScenarioStepStatus.PENDING, ScenarioStepStatus.SKIPPED}:
            if self.started_at is not None or self.finished_at is not None:
                raise ValueError("pending/skipped steps must not have timestamps")
        elif self.status == ScenarioStepStatus.RUNNING:
            if self.started_at is None or self.finished_at is not None:
                raise ValueError("running steps require started_at and must not have finished_at")
        else:
            if self.started_at is None or self.finished_at is None:
                raise ValueError("completed steps require started_at and finished_at")
            if self.finished_at < self.started_at:
                raise ValueError("finished_at must not precede started_at")
        if self.status == ScenarioStepStatus.FAILED and not self.error:
            raise ValueError("failed steps require an error description")
        if self.status == ScenarioStepStatus.PASSED and self.error is not None:
            raise ValueError("passed steps must not have an error description")
        return self


class ScenarioAssertionResult(ScenarioModel):
    assertion_id: str = Field(pattern=_ID_PATTERN)
    status: ScenarioAssertionStatus
    expected: ScenarioExpected
    observed: ScenarioExpected | None = None
    message: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_observed_type(self):
        if self.status == ScenarioAssertionStatus.PASSED and self.observed is None:
            raise ValueError("passed assertions require an observed value")
        if self.observed is not None and type(self.observed) is not type(self.expected):
            raise ValueError("observed value must have the same type as expected")
        return self


class ScenarioRunResult(ScenarioModel):
    scenario: ScenarioDefinition
    run: ScenarioRun
    step_results: list[ScenarioStepResult] = Field(default_factory=list, max_length=50)
    assertion_results: list[ScenarioAssertionResult] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def validate_result_consistency(self):
        if self.run.scenario_id != self.scenario.scenario_id or self.run.scenario_version != self.scenario.version:
            raise ValueError("run must reference the included scenario version")

        step_ids = [result.step_id for result in self.step_results]
        assertion_ids = [result.assertion_id for result in self.assertion_results]
        if len(step_ids) != len(set(step_ids)) or len(assertion_ids) != len(set(assertion_ids)):
            raise ValueError("result identifiers must be unique")

        defined_steps = {step.step_id for step in self.scenario.steps}
        defined_assertions = {assertion.assertion_id: assertion for assertion in self.scenario.assertions}
        if not set(step_ids).issubset(defined_steps) or not set(assertion_ids).issubset(defined_assertions):
            raise ValueError("results must reference IDs defined by the scenario")

        for result in self.assertion_results:
            if result.expected != defined_assertions[result.assertion_id].expected:
                raise ValueError("assertion result expected value must match its definition")

        if self.run.status == ScenarioRunStatus.PASSED:
            if set(step_ids) != defined_steps or any(result.status != ScenarioStepStatus.PASSED for result in self.step_results):
                raise ValueError("passed runs require a passing result for every defined step")
            if set(assertion_ids) != set(defined_assertions) or any(result.status != ScenarioAssertionStatus.PASSED for result in self.assertion_results):
                raise ValueError("passed runs require a passing result for every defined assertion")
        elif self.run.status == ScenarioRunStatus.FAILED:
            has_failure = any(result.status == ScenarioStepStatus.FAILED for result in self.step_results) or any(result.status == ScenarioAssertionStatus.FAILED for result in self.assertion_results)
            if not has_failure and not self.run.failure_reason:
                raise ValueError("failed runs require a failed result or failure_reason")
        return self



class ScenarioRunRecord(ScenarioModel):
    """A stored run paired with its immutable scenario definition snapshot."""

    scenario: ScenarioDefinition
    run: ScenarioRun
    schema_version: int = Field(default=1, ge=1)
    snapshot_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_snapshot_reference(self):
        if self.run.scenario_id != self.scenario.scenario_id or self.run.scenario_version != self.scenario.version:
            raise ValueError("run record must reference its included scenario snapshot")
        return self
