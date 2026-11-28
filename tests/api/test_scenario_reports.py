from datetime import datetime, timezone
from decimal import Decimal

from app.domain.scenarios import (
    ScenarioAction, ScenarioAssertionDefinition, ScenarioAssertionKind,
    ScenarioDefinition, ScenarioStepDefinition,
)
from app.repositories.postgres_scenario_repository import PostgresScenarioRepository
from app.services.scenario_runner import ScenarioRunner

NOW = datetime(2026, 11, 28, 3, 30, tzinfo=timezone.utc)


def sample_definition():
    return ScenarioDefinition(
        scenario_id="report-api-scenario", name="Synthetic report API scenario", version=1,
        tags=["synthetic"],
        steps=[ScenarioStepDefinition(step_id="observe", action=ScenarioAction.VERIFY)],
        assertions=[
            ScenarioAssertionDefinition(assertion_id="count", kind=ScenarioAssertionKind.TRANSACTION_COUNT, expected=1),
            ScenarioAssertionDefinition(assertion_id="amount", kind=ScenarioAssertionKind.AMOUNT_INVARIANT, expected=Decimal("10.00")),
        ],
        created_at=NOW,
    )


def submit_terminal_evidence(client, db_session):
    repository = PostgresScenarioRepository(db_session)
    definition = sample_definition()
    repository.add_definition(definition)
    created = client.post("/api/v1/scenarios/report-api-scenario/versions/1/runs")
    assert created.status_code == 201, created.text
    run_id = created.json()["run"]["run_id"]
    result = ScenarioRunner(
        {ScenarioAction.VERIFY: lambda p, o: {"transaction_count": 1, "amount_invariant": Decimal("10.00")}},
        clock=lambda: NOW,
    ).run(definition, run_id=run_id)
    body = repository._evidence_json(result.model_dump(mode="python"))
    response = client.post(f"/api/v1/scenario-runs/{run_id}/evidence", json=body)
    assert response.status_code == 200, response.text
    return run_id


def test_report_endpoint_returns_versioned_machine_readable_summary(client, db_session):
    run_id = submit_terminal_evidence(client, db_session)
    response = client.get(f"/api/v1/scenario-runs/{run_id}/report")
    assert response.status_code == 200, response.text
    report = response.json()
    assert report["report_schema_version"] == 1
    assert report["scenario_storage_schema_version"] == 1
    assert report["run"]["run_id"] == run_id
    assert report["summary"]["status"] == "passed"
    assert report["summary"]["total_steps"] == report["summary"]["passed_steps"] == 1
    assert report["summary"]["failed_steps"] == report["summary"]["skipped_steps"] == 0
    assert report["summary"]["total_assertions"] == report["summary"]["passed_assertions"] == 2
    assert report["summary"]["failed_assertions"] == report["summary"]["skipped_assertions"] == 0
    assert len(report["snapshot_sha256"]) == 64
    assert [event["sequence"] for event in report["timeline"]] == list(range(1, len(report["timeline"]) + 1))
    assert report["step_results"][0]["step_id"] == "observe"


def test_report_schema_endpoint_is_versioned(client):
    schema = client.get("/api/v1/scenario-run-reports/schema/1")
    assert schema.status_code == 200, schema.text
    payload = schema.json()
    assert payload["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert payload["properties"]["report_schema_version"]["const"] == 1
    assert client.get("/api/v1/scenario-run-reports/schema/2").status_code == 404


def test_report_endpoint_distinguishes_missing_and_pending_runs(client, db_session):
    missing = "00000000-0000-0000-0000-000000000000"
    assert client.get(f"/api/v1/scenario-runs/{missing}/report").status_code == 404
    repository = PostgresScenarioRepository(db_session)
    repository.add_definition(sample_definition())
    created = client.post("/api/v1/scenarios/report-api-scenario/versions/1/runs")
    run_id = created.json()["run"]["run_id"]
    pending = client.get(f"/api/v1/scenario-runs/{run_id}/report")
    assert pending.status_code == 409
