from datetime import datetime, timezone
from decimal import Decimal

from app.domain.scenarios import (
    ScenarioAction, ScenarioAssertionDefinition, ScenarioAssertionKind,
    ScenarioDefinition, ScenarioStepDefinition,
)
from app.repositories.postgres_scenario_repository import PostgresScenarioRepository
from app.services.scenario_runner import ScenarioRunner

NOW = datetime(2026, 11, 27, 3, 30, tzinfo=timezone.utc)


def sample_definition():
    return ScenarioDefinition(
        scenario_id="evidence-scenario", name="Synthetic evidence capture", version=1,
        tags=["synthetic"],
        steps=[ScenarioStepDefinition(step_id="observe", action=ScenarioAction.VERIFY)],
        assertions=[
            ScenarioAssertionDefinition(assertion_id="count", kind=ScenarioAssertionKind.TRANSACTION_COUNT, target_step_id="observe", expected=1),
            ScenarioAssertionDefinition(assertion_id="amount", kind=ScenarioAssertionKind.AMOUNT_INVARIANT, target_step_id="observe", expected=Decimal("10.00")),
        ], created_at=NOW,
    )


def build_result(definition, run_id):
    handler = lambda p, o: {"transaction_count": 1, "amount_invariant": Decimal("10.00")}
    return ScenarioRunner({ScenarioAction.VERIFY: handler}, clock=lambda: NOW).run(definition, run_id=run_id)


def test_create_run_submit_query_evidence_and_order_timeline(client, db_session):
    repository = PostgresScenarioRepository(db_session)
    definition = sample_definition()
    repository.add_definition(definition)
    create = client.post("/api/v1/scenarios/evidence-scenario/versions/1/runs")
    assert create.status_code == 201, create.text
    run_id = create.json()["run"]["run_id"]
    result = build_result(definition, run_id)
    body = repository._evidence_json(result.model_dump(mode="python"))
    submit = client.post(f"/api/v1/scenario-runs/{run_id}/evidence", json=body)
    assert submit.status_code == 200, submit.text
    assert submit.json()["run"]["status"] == "passed"

    evidence = client.get(f"/api/v1/scenario-runs/{run_id}/evidence")
    assert evidence.status_code == 200, evidence.text
    assert evidence.json()["run"]["status"] == "passed"
    assert [item["step_id"] for item in evidence.json()["step_results"]] == ["observe"]
    assert [item["assertion_id"] for item in evidence.json()["assertion_results"]] == ["count", "amount"]

    timeline = client.get(f"/api/v1/scenario-runs/{run_id}/timeline")
    assert timeline.status_code == 200, timeline.text
    events = timeline.json()
    assert [event["sequence"] for event in events] == list(range(1, len(events) + 1))
    assert events[0]["event_type"] == "run_started"
    assert events[-1]["event_type"] == "run_completed"
    assert any(event["event_type"] == "step_completed" for event in events)
    assert any(event["event_type"] == "assertion_evaluated" for event in events)

    duplicate = client.post(f"/api/v1/scenario-runs/{run_id}/evidence", json=body)
    assert duplicate.status_code == 409


def test_missing_run_and_pending_evidence_are_not_reported_as_complete(client, db_session):
    missing = "00000000-0000-0000-0000-000000000000"
    assert client.get(f"/api/v1/scenario-runs/{missing}/timeline").status_code == 404
    definition = sample_definition()
    PostgresScenarioRepository(db_session).add_definition(definition)
    create = client.post("/api/v1/scenarios/evidence-scenario/versions/1/runs")
    run_id = create.json()["run"]["run_id"]
    assert client.get(f"/api/v1/scenario-runs/{run_id}/evidence").status_code == 409


def test_evidence_submission_rejects_snapshot_mismatch(client, db_session):
    repository = PostgresScenarioRepository(db_session)
    definition = sample_definition()
    repository.add_definition(definition)
    create = client.post("/api/v1/scenarios/evidence-scenario/versions/1/runs")
    run_id = create.json()["run"]["run_id"]
    altered = definition.model_copy(update={"name": "Altered snapshot"})
    result = build_result(altered, run_id)
    body = repository._evidence_json(result.model_dump(mode="python"))
    response = client.post(f"/api/v1/scenario-runs/{run_id}/evidence", json=body)
    assert response.status_code == 422
