"""One durable read of the workflow per turn, scoped to this request/thread."""
from contextlib import contextmanager
from contextvars import ContextVar

from config import BQ_DATASET, BQ_PROJECT
from core.production.repository import get_production as read_production
from core.production import workflow_repository as repo
from utils.bigquery_utils import query_bq

_CURRENT = ContextVar("monthly_pipeline_snapshot", default=None)
TABLE = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_PRODUCTION_ARTIFACT"


def read_artifacts(production_id):
    rows = query_bq(f"""
        SELECT * FROM `{TABLE}` WHERE PRODUCTION_ID=@id
        ORDER BY VERSION_NUMBER DESC
    """, {"id": production_id}) or []
    result = [repo._out(row) for row in rows]
    if len({item["artifact_id"] for item in result}) != len(result):
        raise ValueError("Identifiants de workflow dupliqués dans le suivi Monthly.")
    return result


@contextmanager
def pipeline_scope(production_id):
    current = _CURRENT.get()
    if current and current["production_id"] == production_id:
        yield current
        return
    state = {"production_id": production_id, "production": read_production(production_id),
             "artifacts": {item["artifact_id"]: item for item in read_artifacts(production_id)}}
    token = _CURRENT.set(state)
    try:
        yield state
    finally:
        _CURRENT.reset(token)


def get_production(production_id):
    state = _CURRENT.get()
    return state["production"] if state and state["production_id"] == production_id else read_production(production_id)


def get_artifact(production_id, artifact_id):
    state = _CURRENT.get()
    if state and state["production_id"] == production_id:
        return state["artifacts"].get(artifact_id)
    return repo.get_artifact(production_id, artifact_id)


def history(production_id):
    state = _CURRENT.get()
    if state and state["production_id"] == production_id:
        return sorted(state["artifacts"].values(), key=lambda item: item["version_number"], reverse=True)
    return read_artifacts(production_id)


def remember(item):
    state = _CURRENT.get()
    if state and item and state["production_id"] == item["production_id"]:
        state["artifacts"][item["artifact_id"]] = item


def cached_production(production_id):
    state = _CURRENT.get()
    return state["production"] if state and state["production_id"] == production_id else None
