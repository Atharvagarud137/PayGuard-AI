from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.domain.scenarios import ScenarioAction, ScenarioAssertionDefinition, ScenarioAssertionKind, ScenarioDefinition, ScenarioRunStatus, ScenarioStepDefinition
from app.repositories.postgres_scenario_repository import PostgresScenarioRepository, payload_sha256


NOW = datetime(2026, 11, 24, 9, 0, tzinfo=timezone.utc)


def sample_definition(version: int = 1, name: str = "Response-loss retry") -> ScenarioDefinition:
    return ScenarioDefinition(
        scenario_id="response-loss-retry", name=name, version=version,
        description="Synthetic persistence test", tags=["synthetic", "retry"],
        steps=[ScenarioStepDefinition(step_id="verify", action=ScenarioAction.VERIFY,
                                     parameters={"merchant_id": "synthetic-merchant"})],
        assertions=[ScenarioAssertionDefinition(assertion_id="operation-count",
                                               kind=ScenarioAssertionKind.TRANSACTION_COUNT,
                                               expected=0)],
        created_at=NOW,
    )


def test_definition_round_trip_and_digest(db_session):
    repository = PostgresScenarioRepository(db_session)
    definition = sample_definition()
    repository.add_definition(definition)
    retrieved = repository.get_definition(definition.scenario_id, definition.version)
    assert retrieved == definition
    assert payload_sha256(definition.model_dump(mode="json"))


def test_definition_versions_are_insert_only_and_ordered(db_session):
    repository = PostgresScenarioRepository(db_session)
    repository.add_definition(sample_definition(version=2, name="Version two"))
    repository.add_definition(sample_definition(version=1, name="Version one"))
    versions = repository.list_versions("response-loss-retry")
    assert [definition.version for definition in versions] == [1, 2]
    assert [definition.name for definition in versions] == ["Version one", "Version two"]
    with pytest.raises(IntegrityError):
        repository.add_definition(sample_definition(version=1, name="Overwrite attempt"))
    db_session.rollback()


def test_missing_definition_returns_none(db_session):
    repository = PostgresScenarioRepository(db_session)
    assert repository.get_definition("missing-scenario", 1) is None
    assert repository.list_versions("missing-scenario") == []


def test_create_run_uses_persisted_version_and_round_trips_snapshot(db_session):
    repository = PostgresScenarioRepository(db_session)
    definition = sample_definition()
    repository.add_definition(definition)
    record = repository.create_run(definition.scenario_id, definition.version)
    retrieved = repository.get_run(str(record.run.run_id))
    assert retrieved is not None
    assert retrieved.run.status == ScenarioRunStatus.PENDING
    assert retrieved.run.scenario_id == definition.scenario_id
    assert retrieved.run.scenario_version == definition.version
    assert retrieved.scenario == definition
    assert retrieved.snapshot_sha256 == record.snapshot_sha256
    assert retrieved.schema_version == 1


def test_run_snapshot_remains_bound_to_its_definition_version(db_session):
    repository = PostgresScenarioRepository(db_session)
    version_one = sample_definition(version=1, name="Original")
    repository.add_definition(version_one)
    run = repository.create_run(version_one.scenario_id, version_one.version)
    repository.add_definition(sample_definition(version=2, name="Changed"))
    retrieved = repository.get_run(str(run.run.run_id))
    assert retrieved.scenario.version == 1
    assert retrieved.scenario.name == "Original"
    assert retrieved.run.scenario_version == 1


def test_run_listing_filters_and_paginates(db_session):
    repository = PostgresScenarioRepository(db_session)
    definition = sample_definition()
    repository.add_definition(definition)
    first = repository.create_run(definition.scenario_id, 1)
    second = repository.create_run(definition.scenario_id, 1)
    runs = repository.list_runs(scenario_id=definition.scenario_id, status="pending", limit=1)
    assert len(runs) == 1
    page_two = repository.list_runs(scenario_id=definition.scenario_id, limit=1, offset=1)
    assert len(page_two) == 1
    assert page_two[0].run.run_id != runs[0].run.run_id
    assert repository.get_run(str(first.run.run_id)) is not None
    assert repository.get_run(str(second.run.run_id)) is not None


def test_run_creation_rejects_missing_definition_and_invalid_pagination(db_session):
    repository = PostgresScenarioRepository(db_session)
    with pytest.raises(ValueError, match="does not exist"):
        repository.create_run("missing-scenario", 1)
    with pytest.raises(ValueError, match="limit"):
        repository.list_runs(limit=0)
    with pytest.raises(ValueError, match="scenario_version requires"):
        repository.list_runs(scenario_version=1)


def test_digest_detects_changed_payload():
    original = sample_definition().model_dump(mode="json")
    changed = dict(original)
    changed["name"] = "Altered"
    assert payload_sha256(original) != payload_sha256(changed)
