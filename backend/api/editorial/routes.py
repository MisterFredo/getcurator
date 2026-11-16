import logging
from datetime import date as CalendarDate
from datetime import datetime
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from openai import APIError
from pydantic import BaseModel, ConfigDict, Field

from core.editorial import repository, service
from core.editorial.weekly_review import ReviewUnavailable, build_weekly_review

logger = logging.getLogger(__name__)


router = APIRouter()


class StartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    date: CalendarDate
    request_id: UUID


class BulkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID
    mode: Literal["selected_dates", "current_month"]
    dates: list[CalendarDate] = Field(default_factory=list, max_length=31)


class RecoverRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    response_id: str = Field(pattern=r"^resp_[a-zA-Z0-9_]+$", max_length=200)


class WeeklyReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    week_end: CalendarDate
    available_from: CalendarDate


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


@router.post("/daily-bulk-jobs", status_code=202)
def start_daily_bulk(payload: BulkRequest, background_tasks: BackgroundTasks):
    results = action(service.start_bulk, payload.mode, payload.dates, str(payload.request_id))
    for result in results:
        job = result.get("job")
        if job and job["status"] == "in_progress":
            background_tasks.add_task(submit_background, job["job_id"])
    return {"results": results}


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


@router.post("/weekly-reviews")
def weekly_review(request: WeeklyReviewRequest):
    if request.week_end.weekday() != 6 or request.available_from.weekday() != 0:
        raise HTTPException(422, "Choisis un dimanche de clôture et un lundi de début de couverture.")
    if request.available_from > request.week_end:
        raise HTTPException(422, "Le début de couverture doit précéder la fin de semaine.")
    if request.week_end >= datetime.now(ZoneInfo("Europe/Paris")).date():
        raise HTTPException(422, "La semaine sélectionnée n’est pas terminée.")
    try:
        return build_weekly_review(request.week_end, request.available_from)
    except ReviewUnavailable as exc:
        raise HTTPException(502, str(exc)) from exc
