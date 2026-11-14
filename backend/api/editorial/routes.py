import logging
from datetime import date as CalendarDate
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from openai import APIError
from pydantic import BaseModel, ConfigDict, Field

from core.editorial import repository, service
from core.user.user_service import get_user_by_id
from utils.auth import get_user_id_from_request

logger = logging.getLogger(__name__)


def require_admin(request: Request):
    user_id = get_user_id_from_request(request)
    user = get_user_by_id(user_id) if user_id else None
    if not user:
        raise HTTPException(status_code=401, detail="Authentification requise.")
    if str(user.get("ROLE") or "").strip().lower() != "admin":
        raise HTTPException(status_code=403, detail="Accès administrateur requis.")


router = APIRouter(dependencies=[Depends(require_admin)])


class StartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    date: CalendarDate
    request_id: UUID


class RecoverRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    response_id: str = Field(pattern=r"^resp_[a-zA-Z0-9_]+$", max_length=200)


def action(call, *args):
    try:
        return call(*args)
    except service.Conflict as exc:
        raise HTTPException(409, str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except APIError as exc:
        logger.exception("Fournisseur Editorial indisponible")
        raise HTTPException(502, "Fournisseur indisponible. Réessayez l’actualisation.") from exc


def submit_background(job_id):
    try:
        service.refresh(job_id)
    except Exception:
        logger.exception("Traitement Editorial interrompu job=%s", job_id)


@router.post("/daily-jobs", status_code=202)
def start_daily_job(payload: StartRequest, background_tasks: BackgroundTasks):
    job = action(service.start, payload.date.isoformat(), str(payload.request_id))
    if job["status"] == "in_progress":
        background_tasks.add_task(submit_background, job["job_id"])
    return {"job": job}


@router.get("/daily-jobs/{job_id}")
def read_daily_job(job_id: UUID):
    return {"job": action(service.read_job, str(job_id))}


@router.post("/daily-jobs/{job_id}/refresh")
def refresh_daily_job(job_id: UUID):
    return {"job": action(service.refresh, str(job_id))}


@router.get("/daily-editions")
def list_daily_editions(date: CalendarDate | None = None, universe_id: str | None = None,
                        limit: int = Query(100, ge=1, le=100), offset: int = Query(0, ge=0)):
    day = date.isoformat() if date else None
    return {"editions": action(repository.list_editions, day, universe_id, limit, offset)}


@router.get("/daily-editions/{edition_id}")
def read_daily_edition(edition_id: UUID):
    return {"edition": action(service.edition_detail, str(edition_id))}


@router.post("/daily-editions/{edition_id}/recover")
def recover_daily_edition(edition_id: UUID, payload: RecoverRequest):
    return {"job": action(service.recover, str(edition_id), payload.response_id)}
