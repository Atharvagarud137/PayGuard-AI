"""PostgreSQL persistence for immutable scenario versions and run snapshots."""

import hashlib
import json
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database_models import (
    ScenarioDefinitionDB, ScenarioRunDB, ScenarioStepEvidenceDB,
    ScenarioAssertionEvidenceDB, ScenarioRunEventDB,
)
from app.domain.scenarios import (
    ScenarioAssertionResult, ScenarioAssertionStatus, ScenarioDefinition, ScenarioRun,
    ScenarioRunEvent, ScenarioRunResult, ScenarioRunStatus, ScenarioStepResult,
    ScenarioStepStatus, ScenarioEventType,
)


SCHEMA_VERSION = 1
MAX_SCENARIO_PAYLOAD_BYTES = 64 * 1024


class ScenarioStorageIntegrityError(RuntimeError):
    """Raised when persisted scenario JSON or metadata fails integrity checks."""


def canonical_json(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def payload_sha256(payload: dict) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def _json_default(value):
    if isinstance(value, Decimal):
        return {"$decimal": str(value)}
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    raise TypeError(f"unsupported scenario payload value: {type(value).__name__}")


def scenario_payload(definition: ScenarioDefinition) -> dict:
    """Encode model values without conflating Decimal and ordinary strings."""
    python_payload = definition.model_dump(mode="python")
    encoded = json.dumps(python_payload, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, default=_json_default)
    return json.loads(encoded)


def _restore_decimal_tags(payload):
    if isinstance(payload, dict):
        if set(payload) == {"$decimal"} and isinstance(payload["$decimal"], str):
            return Decimal(payload["$decimal"])
        return {key: _restore_decimal_tags(value) for key, value in payload.items()}
    if isinstance(payload, list):
        return [_restore_decimal_tags(value) for value in payload]
    return payload


def _ensure_payload_size(payload, *, limit: int = MAX_SCENARIO_PAYLOAD_BYTES):
    if len(canonical_json(payload).encode("utf-8")) > limit:
        raise ValueError(f"scenario evidence payload exceeds {limit} bytes")


class PostgresScenarioRepository:
    """Insert-only scenario versions and durable, frozen run snapshots.

    Flushes but never commits. Definition versions and run snapshots are
    immutable; only lifecycle columns are intended to be updated later.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def add_definition(self, definition: ScenarioDefinition, *, schema_version: int = SCHEMA_VERSION) -> ScenarioDefinition:
        if schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported scenario schema version: {schema_version}")
        payload = scenario_payload(definition)
        _ensure_payload_size(payload)
        row = ScenarioDefinitionDB(
            scenario_id=definition.scenario_id,
            version=definition.version,
            schema_version=schema_version,
            name=definition.name,
            description=definition.description,
            tags=list(definition.tags),
            definition_json=payload,
            definition_sha256=payload_sha256(payload),
            created_at=definition.created_at,
        )
        self.db.add(row)
        self.db.flush()
        return definition

    def get_definition(self, scenario_id: str, version: int) -> Optional[ScenarioDefinition]:
        row = self.db.execute(select(ScenarioDefinitionDB).where(
            ScenarioDefinitionDB.scenario_id == scenario_id,
            ScenarioDefinitionDB.version == version,
        )).scalar_one_or_none()
        return None if row is None else self._verify_definition_row(row)

    def list_versions(self, scenario_id: str) -> list[ScenarioDefinition]:
        rows = self.db.execute(select(ScenarioDefinitionDB)
            .where(ScenarioDefinitionDB.scenario_id == scenario_id)
            .order_by(ScenarioDefinitionDB.version.asc())).scalars().all()
        return [self._verify_definition_row(row) for row in rows]

    def create_run(self, scenario_id: str, version: int) -> ScenarioRunRecord:
        definition_row = self.db.execute(select(ScenarioDefinitionDB).where(
            ScenarioDefinitionDB.scenario_id == scenario_id,
            ScenarioDefinitionDB.version == version,
        )).scalar_one_or_none()
        if definition_row is None:
            raise ValueError("scenario definition version does not exist")

        definition = self._verify_definition_row(definition_row)
        payload = scenario_payload(definition)
        _ensure_payload_size(payload)
        digest = payload_sha256(payload)
        run = ScenarioRun(scenario_id=definition.scenario_id, scenario_version=definition.version)
        record = ScenarioRunRecord(
            scenario=definition, run=run,
            schema_version=definition_row.schema_version,
            snapshot_sha256=digest,
        )
        self.db.add(ScenarioRunDB(
            run_id=str(run.run_id),
            scenario_id=run.scenario_id,
            scenario_version=run.scenario_version,
            schema_version=definition_row.schema_version,
            status=run.status.value,
            created_at=run.created_at,
            started_at=run.started_at,
            finished_at=run.finished_at,
            failure_reason=run.failure_reason,
            snapshot_json=payload,
            snapshot_sha256=digest,
        ))
        self.db.flush()
        return record

    def get_run(self, run_id: str) -> Optional[ScenarioRunRecord]:
        row = self.db.execute(select(ScenarioRunDB).where(
            ScenarioRunDB.run_id == run_id,
        )).scalar_one_or_none()
        return None if row is None else self._verify_run_row(row)

    def list_runs(
        self, *, scenario_id: str | None = None, scenario_version: int | None = None,
        status: ScenarioRunStatus | str | None = None, limit: int = 50, offset: int = 0,
    ) -> list[ScenarioRunRecord]:
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("limit must be an integer from 1 to 100")
        if type(offset) is not int or offset < 0:
            raise ValueError("offset must be a non-negative integer")
        if scenario_version is not None and scenario_id is None:
            raise ValueError("scenario_version requires scenario_id")
        statement = select(ScenarioRunDB)
        if scenario_id is not None:
            statement = statement.where(ScenarioRunDB.scenario_id == scenario_id)
        if scenario_version is not None:
            statement = statement.where(ScenarioRunDB.scenario_version == scenario_version)
        if status is not None:
            value = status.value if isinstance(status, ScenarioRunStatus) else ScenarioRunStatus(status).value
            statement = statement.where(ScenarioRunDB.status == value)
        statement = statement.order_by(
            ScenarioRunDB.created_at.desc(), ScenarioRunDB.run_id.desc()
        ).limit(limit).offset(offset)
        rows = self.db.execute(statement).scalars().all()
        return [self._verify_run_row(row) for row in rows]

    @staticmethod
    def _verify_definition_row(row: ScenarioDefinitionDB) -> ScenarioDefinition:
        if row.schema_version != SCHEMA_VERSION:
            raise ScenarioStorageIntegrityError(
                f"unsupported persisted definition schema version: {row.schema_version}"
            )
        payload = row.definition_json
        if not isinstance(payload, dict):
            raise ScenarioStorageIntegrityError("scenario definition payload is not a JSON object")
        try:
            _ensure_payload_size(payload)
        except ValueError as exc:
            raise ScenarioStorageIntegrityError("persisted scenario definition exceeds size limit") from exc
        if payload_sha256(payload) != row.definition_sha256:
            raise ScenarioStorageIntegrityError("scenario definition digest mismatch")
        try:
            definition = ScenarioDefinition.model_validate(_restore_decimal_tags(payload))
        except Exception as exc:
            raise ScenarioStorageIntegrityError("persisted scenario definition is invalid") from exc
        if (definition.scenario_id != row.scenario_id or definition.version != row.version
            or definition.name != row.name or definition.description != row.description
            or list(definition.tags) != list(row.tags or [])):
            raise ScenarioStorageIntegrityError("scenario definition metadata does not match its payload")
        return definition

    @staticmethod
    def _verify_run_row(row: ScenarioRunDB) -> ScenarioRunRecord:
        payload = row.snapshot_json
        if not isinstance(payload, dict):
            raise ScenarioStorageIntegrityError("scenario run snapshot is not a JSON object")
        try:
            _ensure_payload_size(payload)
        except ValueError as exc:
            raise ScenarioStorageIntegrityError("persisted scenario run snapshot exceeds size limit") from exc
        if payload_sha256(payload) != row.snapshot_sha256:
            raise ScenarioStorageIntegrityError("scenario run snapshot digest mismatch")
        try:
            scenario = ScenarioDefinition.model_validate(_restore_decimal_tags(payload))
            run = ScenarioRun(
                run_id=row.run_id, scenario_id=row.scenario_id,
                scenario_version=row.scenario_version, status=ScenarioRunStatus(row.status),
                created_at=row.created_at, started_at=row.started_at,
                finished_at=row.finished_at, failure_reason=row.failure_reason,
            )
            return ScenarioRunRecord(
                scenario=scenario, run=run, schema_version=row.schema_version,
                snapshot_sha256=row.snapshot_sha256,
            )
        except ScenarioStorageIntegrityError:
            raise
        except Exception as exc:
            raise ScenarioStorageIntegrityError(
                "persisted scenario run snapshot or lifecycle is invalid"
            ) from exc

    @staticmethod
    def _evidence_json(value):
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, default=_json_default)
        return json.loads(encoded)

    @staticmethod
    def _coerce_expected_value(value, expected):
        value = _restore_decimal_tags(value)
        if isinstance(expected, Enum):
            return type(expected)(value)
        if isinstance(expected, Decimal) and type(value) is str:
            return Decimal(value)
        return value

    def persist_evidence(self, run_id: str, result: ScenarioRunResult) -> ScenarioRunResult:
        """Atomically store one terminal result, its evidence rows and ordered timeline."""
        row = self.db.execute(select(ScenarioRunDB).where(
            ScenarioRunDB.run_id == run_id,
        ).with_for_update()).scalar_one_or_none()
        if row is None:
            raise ValueError("scenario run does not exist")
        record = self._verify_run_row(row)
        if row.status != ScenarioRunStatus.PENDING.value:
            raise RuntimeError("scenario run is not pending; evidence is immutable")
        if str(result.run.run_id) != row.run_id:
            raise ValueError("evidence run_id does not match the requested run")
        if result.scenario != record.scenario:
            raise ValueError("evidence scenario does not match the frozen run snapshot")
        if result.run.scenario_id != row.scenario_id or result.run.scenario_version != row.scenario_version:
            raise ValueError("evidence scenario identifiers do not match the stored run")
        if result.run.status not in {ScenarioRunStatus.PASSED, ScenarioRunStatus.FAILED}:
            raise ValueError("only terminal passed/failed runner results can be persisted")
        if result.run.started_at is None or result.run.finished_at is None:
            raise ValueError("terminal evidence requires run timestamps")

        defined_step_ids = [step.step_id for step in record.scenario.steps]
        defined_assertion_ids = [assertion.assertion_id for assertion in record.scenario.assertions]
        if set(item.step_id for item in result.step_results) != set(defined_step_ids):
            raise ValueError("evidence must contain exactly one result for every defined step")
        if set(item.assertion_id for item in result.assertion_results) != set(defined_assertion_ids):
            raise ValueError("evidence must contain exactly one result for every defined assertion")
        if not result.events or result.events[0].event_type != ScenarioEventType.RUN_STARTED or result.events[-1].event_type != ScenarioEventType.RUN_COMPLETED:
            raise ValueError("evidence must include a complete run timeline")
        if result.events[0].occurred_at != result.run.started_at or result.events[-1].occurred_at != result.run.finished_at:
            raise ValueError("timeline start/end events must match run timestamps")

        defined_assertions = {item.assertion_id: item for item in record.scenario.assertions}
        for assertion_result in result.assertion_results:
            if assertion_result.expected != defined_assertions[assertion_result.assertion_id].expected:
                raise ValueError("assertion expected value does not match the frozen definition")
        for event in result.events:
            if event.step_id is not None and event.step_id not in set(defined_step_ids):
                raise ValueError("timeline event references an unknown step")
            if event.assertion_id is not None and event.assertion_id not in set(defined_assertion_ids):
                raise ValueError("timeline event references an unknown assertion")

        row.status = result.run.status.value
        row.started_at = result.run.started_at
        row.finished_at = result.run.finished_at
        row.failure_reason = result.run.failure_reason
        step_order = {step_id: ordinal for ordinal, step_id in enumerate(defined_step_ids, start=1)}
        assertion_order = {assertion_id: ordinal for ordinal, assertion_id in enumerate(defined_assertion_ids, start=1)}
        for step_result in result.step_results:
            output_json = self._evidence_json(step_result.output)
            _ensure_payload_size(output_json)
            self.db.add(ScenarioStepEvidenceDB(
                run_id=row.run_id, step_id=step_result.step_id,
                ordinal=step_order[step_result.step_id], status=step_result.status.value,
                started_at=step_result.started_at, finished_at=step_result.finished_at,
                output_json=output_json, error=step_result.error,
            ))
        for assertion_result in result.assertion_results:
            expected_json = self._evidence_json(assertion_result.expected)
            observed_json = None if assertion_result.observed is None else self._evidence_json(assertion_result.observed)
            _ensure_payload_size(expected_json)
            if observed_json is not None:
                _ensure_payload_size(observed_json)
            self.db.add(ScenarioAssertionEvidenceDB(
                run_id=row.run_id, assertion_id=assertion_result.assertion_id,
                ordinal=assertion_order[assertion_result.assertion_id],
                status=assertion_result.status.value, expected_json=expected_json,
                observed_json=observed_json, message=assertion_result.message,
            ))
        for event in result.events:
            payload_json = self._evidence_json(event.payload)
            _ensure_payload_size(payload_json, limit=4096)
            self.db.add(ScenarioRunEventDB(
                run_id=row.run_id, sequence=event.sequence,
                event_type=event.event_type.value, occurred_at=event.occurred_at,
                step_id=event.step_id, assertion_id=event.assertion_id,
                payload_json=payload_json,
            ))
        self.db.flush()
        stored = self.get_evidence(row.run_id)
        if stored is None:
            raise ScenarioStorageIntegrityError("persisted evidence could not be reconstructed")
        return stored

    def get_evidence(self, run_id: str) -> Optional[ScenarioRunResult]:
        row = self.db.execute(select(ScenarioRunDB).where(
            ScenarioRunDB.run_id == run_id,
        )).scalar_one_or_none()
        if row is None or row.status == ScenarioRunStatus.PENDING.value:
            return None
        record = self._verify_run_row(row)
        step_rows = self.db.execute(select(ScenarioStepEvidenceDB).where(
            ScenarioStepEvidenceDB.run_id == run_id,
        ).order_by(ScenarioStepEvidenceDB.ordinal.asc())).scalars().all()
        assertion_rows = self.db.execute(select(ScenarioAssertionEvidenceDB).where(
            ScenarioAssertionEvidenceDB.run_id == run_id,
        ).order_by(ScenarioAssertionEvidenceDB.ordinal.asc())).scalars().all()
        event_rows = self.db.execute(select(ScenarioRunEventDB).where(
            ScenarioRunEventDB.run_id == run_id,
        ).order_by(ScenarioRunEventDB.sequence.asc())).scalars().all()
        if not step_rows or not assertion_rows or not event_rows:
            return None

        step_results = [
            ScenarioStepResult(
                step_id=item.step_id, status=ScenarioStepStatus(item.status),
                started_at=item.started_at, finished_at=item.finished_at,
                output=_restore_decimal_tags(item.output_json), error=item.error,
            )
            for item in step_rows
        ]
        defined_assertions = {item.assertion_id: item for item in record.scenario.assertions}
        assertion_results = []
        for item in assertion_rows:
            definition = defined_assertions.get(item.assertion_id)
            if definition is None:
                raise ScenarioStorageIntegrityError("stored assertion evidence references an unknown assertion")
            expected_stored = self._coerce_expected_value(item.expected_json, definition.expected)
            if expected_stored != definition.expected:
                raise ScenarioStorageIntegrityError("stored assertion expected value differs from definition")
            observed = None if item.observed_json is None else self._coerce_expected_value(item.observed_json, definition.expected)
            assertion_results.append(ScenarioAssertionResult(
                assertion_id=item.assertion_id, status=ScenarioAssertionStatus(item.status),
                expected=definition.expected, observed=observed, message=item.message,
            ))
        events = [
            ScenarioRunEvent(
                sequence=item.sequence, event_type=ScenarioEventType(item.event_type),
                occurred_at=item.occurred_at, step_id=item.step_id,
                assertion_id=item.assertion_id, payload=_restore_decimal_tags(item.payload_json),
            )
            for item in event_rows
        ]
        return ScenarioRunResult(
            scenario=record.scenario, run=record.run,
            step_results=step_results, assertion_results=assertion_results, events=events,
        )

    def list_events(self, run_id: str) -> list[ScenarioRunEvent]:
        rows = self.db.execute(select(ScenarioRunEventDB).where(
            ScenarioRunEventDB.run_id == run_id,
        ).order_by(ScenarioRunEventDB.sequence.asc())).scalars().all()
        return [
            ScenarioRunEvent(
                sequence=item.sequence, event_type=ScenarioEventType(item.event_type),
                occurred_at=item.occurred_at, step_id=item.step_id,
                assertion_id=item.assertion_id, payload=_restore_decimal_tags(item.payload_json),
            )
            for item in rows
        ]
