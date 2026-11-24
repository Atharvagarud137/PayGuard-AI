"""PostgreSQL persistence for immutable scenario versions and run snapshots."""

import hashlib
import json
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database_models import ScenarioDefinitionDB, ScenarioRunDB
from app.domain.scenarios import ScenarioDefinition, ScenarioRun, ScenarioRunRecord, ScenarioRunStatus


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


def _ensure_payload_size(payload: dict):
    if len(canonical_json(payload).encode("utf-8")) > MAX_SCENARIO_PAYLOAD_BYTES:
        raise ValueError("scenario payload exceeds 64 KiB")


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
