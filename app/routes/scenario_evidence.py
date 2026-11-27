"""Scenario run creation and durable execution-evidence APIs."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.scenarios import ScenarioRunResult
from app.repositories.postgres_scenario_repository import PostgresScenarioRepository

router = APIRouter(prefix="/api/v1", tags=["Scenario evidence"])


@router.post("/scenarios/{scenario_id}/versions/{version}/runs", status_code=201)
def create_scenario_run(scenario_id: str, version: int, db: Session = Depends(get_db)):
    repository = PostgresScenarioRepository(db)
    try:
        record = repository.create_run(scenario_id, version)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return jsonable_encoder(record)


@router.post("/scenario-runs/{run_id}/evidence")
def persist_scenario_evidence(run_id: UUID, result: ScenarioRunResult, db: Session = Depends(get_db)):
    repository = PostgresScenarioRepository(db)
    try:
        stored = repository.persist_evidence(str(run_id), result)
        db.commit()
    except RuntimeError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return jsonable_encoder(stored)


@router.get("/scenario-runs/{run_id}/evidence")
def get_scenario_evidence(run_id: UUID, db: Session = Depends(get_db)):
    repository = PostgresScenarioRepository(db)
    stored = repository.get_evidence(str(run_id))
    if stored is None:
        run = repository.get_run(str(run_id))
        if run is None:
            raise HTTPException(status_code=404, detail="Scenario run not found")
        raise HTTPException(status_code=409, detail="Scenario run has no persisted terminal evidence")
    return jsonable_encoder(stored)


@router.get("/scenario-runs/{run_id}/timeline")
def get_scenario_timeline(run_id: UUID, db: Session = Depends(get_db)):
    repository = PostgresScenarioRepository(db)
    run = repository.get_run(str(run_id))
    if run is None:
        raise HTTPException(status_code=404, detail="Scenario run not found")
    return jsonable_encoder(repository.list_events(str(run_id)))
