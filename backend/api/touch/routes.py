from fastapi import (
    APIRouter,
    HTTPException,
    Query,
)
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from core.touch.edition_bulk_service import (
    bootstrap_all_expert_touch_editions,
)

from core.touch.edition_service import (
    bootstrap_expert_touch_editions,
)

from core.touch.edition_repository import (
    get_touch_edition,
    reopen_touch_edition,
    link_touch_edition_report,
    list_touch_editions,
    update_touch_edition_corpus,
    delete_touch_edition,
)

from core.touch.search_models import (
    TouchResearchBrief,
)

from core.touch.search_service import (
    search_touch_contents,
)

from core.touch.guided_research_models import (
    TouchGuidedResearchRequest,
)

from core.touch.guided_research_service import (
    continue_touch_guided_research,
)

from core.touch.generation_models import (
    TouchGenerationRequest,
)

from core.touch.generation_service import (
    generate_touch_one_pager,
)

from core.touch.notebook_models import (
    TouchCorpusNotebook,
    TouchNotebookRequest,
)

from core.touch.notebook_service import (
    build_touch_notebook,
)

from core.touch.brief_models import (
    TouchBriefRequest,
)

from core.touch.brief_service import (
    build_touch_brief,
)

from core.touch.notebook_report_service import (
    get_touch_report,
    list_touch_reports,
    delete_touch_report,
    set_touch_report_archived,
)

from core.touch.notebook_plan_service import (
    validate_executive_summary,
    validate_notebook,
)

from core.touch.notebook_report_service import (
    save_touch_report,
)


router = APIRouter()

# ============================================================
# SEARCH
# ============================================================

@router.post("/search")
def search_touch(
    brief: TouchResearchBrief,
    response_mode: Literal[
        "full",
        "analysis",
        "consolidation",
    ] = "full",
):

    if not brief.query.strip():

        raise HTTPException(
            status_code=400,
            detail=(
                "La demande de recherche "
                "ne peut pas être vide."
            ),
        )

    try:

        outcome = search_touch_contents(
            brief=brief,
        )

        response = outcome.model_dump(
            mode="json",
        )

        # ====================================================
        # LIGHT CANDIDATE RESPONSE
        # ====================================================

        internal_fields = {

            "content_body",

            "signal_analytique",

            "mecanique_expliquee",

            "enjeu_strategique",

            "point_de_friction",

            "chiffres",

        }

        for candidate in response.get(
            "candidates",
            [],
        ):

            for field_name in internal_fields:

                candidate.pop(
                    field_name,
                    None,
                )

        # ====================================================
        # RESPONSE MODE
        # ====================================================

        if response_mode in (
            "analysis",
            "consolidation",
        ):

            response.pop(
                "candidates",
                None,
            )

        if response_mode == "consolidation":

            response.pop(
                "evaluation",
                None,
            )

        return {

            "status":
                "ok",

            "search":
                response,

        }

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(
                exc
            ),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Erreur lors de la recherche "
                f"éditoriale Touch : {exc}"
            ),
        ) from exc

# ============================================================
# GUIDED RESEARCH
# ============================================================

@router.post("/research-guide")
def guide_touch_research(
    request: TouchGuidedResearchRequest,
):

    try:

        outcome = (
            continue_touch_guided_research(
                request=request,
            )
        )

        return {

            "status":
                "ok",

            "guided_research":
                outcome.model_dump(
                    mode="json",
                ),

        }

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(
                exc
            ),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Erreur lors du cadrage "
                "guidé Touch : "
                f"{exc}"
            ),
        ) from exc

# ============================================================
# BUILD EDITORIAL NOTEBOOK
# ============================================================

@router.post("/notebook")
def build_editorial_notebook(
    request: TouchNotebookRequest,
):

    outcome = build_touch_notebook(
        request=request,
    )

    return {
        "status": "ok",
        "notebook_generation":
            outcome.model_dump(
                mode="json",
            ),
    }


class TouchReportSaveRequest(BaseModel):
    request: TouchNotebookRequest
    notebook: TouchCorpusNotebook


@router.post("/reports")
def save_editorial_report(
    payload: TouchReportSaveRequest,
):
    allowed_content_ids = set(
        payload.request.content_ids
    )

    try:
        validate_notebook(
            notebook=payload.notebook,
            allowed_content_ids=allowed_content_ids,
        )

        validate_executive_summary(
            notebook=payload.notebook,
            allowed_content_ids=allowed_content_ids,
        )

        report_id = save_touch_report(
            request=payload.request,
            notebook=payload.notebook,
            report_id=payload.request.report_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return {
        "status": "ok",
        "report_id": report_id,
    }



@router.get("/reports")
def list_editorial_reports(
    archive: Literal["active", "archived", "all"] = "active",
):
    return {
        "status": "ok",
        "reports": list_touch_reports(archive=archive),
    }


@router.get("/reports/{report_id}")
def get_editorial_report(report_id: str):
    report = get_touch_report(report_id)

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Rapport Touch introuvable.",
        )

    return {
        "status": "ok",
        "report": report,
    }

# ============================================================
# BUILD EDITORIAL BRIEF
# ============================================================

@router.post("/brief")
def build_editorial_brief(
    request: TouchBriefRequest,
):

    outcome = build_touch_brief(
        request=request,
    )

    return {
        "status": "ok",
        "brief_generation":
            outcome.model_dump(
                mode="json",
            ),
    }


# ============================================================
# GENERATE ONE-PAGER
# ============================================================

@router.post("/generate")
def generate_touch(
    request: TouchGenerationRequest,
):

    if not request.subject.strip():

        raise HTTPException(
            status_code=400,
            detail=(
                "Le sujet du one-pager "
                "ne peut pas être vide."
            ),
        )

    if not request.content_ids:

        raise HTTPException(
            status_code=400,
            detail=(
                "Le corpus du one-pager "
                "ne peut pas être vide."
            ),
        )

    outcome = generate_touch_one_pager(
        request=request,
    )

    if (
        outcome.status
        == "GENERATION_FAILED"
    ):

        raise HTTPException(
            status_code=500,
            detail=(
                outcome.error
                or (
                    "La génération du one-pager "
                    "a échoué."
                )
            ),
        )

    return {

        "status":
            "ok",

        "generation":
            outcome.model_dump(
                mode="json",
            ),

    }

# ============================================================
# DELETE SAVED TOUCH REPORT
# ============================================================

@router.delete("/reports/{report_id}")
def delete_saved_touch_report(
    report_id: str,
):

    deleted = delete_touch_report(
        report_id=report_id,
    )

    if not deleted:

        raise HTTPException(
            status_code=404,
            detail="Touch report not found.",
        )

    return {
        "status": "ok",
        "report_id": report_id,
    }


# ============================================================
# PAYLOADS
# ============================================================

class TouchEditionPrepareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expert_id: str | None = None
    months_count: Literal[1, 3] = 3

    @field_validator("expert_id")
    @classmethod
    def validate_expert_id(cls, value):
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Identifiant expert vide.")
        return value


class TouchEditionCorpusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selected_content_ids: list[str] = Field(default_factory=list)
    dismissed_content_ids: list[str] = Field(default_factory=list)


# ============================================================
# LIGHT EDITION RESPONSE
# ============================================================

def _public_admin_edition(edition: dict) -> dict:
    """Same lightweight candidate representation as /touch/search."""
    result = dict(edition)
    search = result.get("search")
    if search is None:
        return result

    search = dict(search)
    internal_fields = {
        "content_body", "signal_analytique", "mecanique_expliquee",
        "enjeu_strategique", "point_de_friction", "chiffres",
    }
    search["candidates"] = [
        {
            key: value
            for key, value in candidate.items()
            if key not in internal_fields
        }
        for candidate in search.get("candidates", [])
    ]
    result["search"] = search
    return result


# ============================================================
# PREPARE ONE OR ALL EXPERTS
# ============================================================

@router.post("/editions/prepare")
def prepare_touch_editions(payload: TouchEditionPrepareRequest):
    try:
        if payload.expert_id is not None:
            preparation = bootstrap_expert_touch_editions(
                expert_id=payload.expert_id,
                months_count=payload.months_count,
            )
        else:
            preparation = bootstrap_all_expert_touch_editions(
                months_count=payload.months_count,
            )
        return {"status": "ok", "preparation": preparation}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur de préparation des éditions Touch : {exc}",
        ) from exc


# ============================================================
# LIST AND OPEN EDITIONS
# ============================================================

@router.get("/editions")
def list_monthly_touch_editions(
    expert_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=200),
):
    return {
        "status": "ok",
        "editions": list_touch_editions(expert_id=expert_id, limit=limit),
    }


@router.get("/editions/{edition_id}")
def get_monthly_touch_edition(edition_id: str):
    edition = get_touch_edition(edition_id)
    if edition is None:
        raise HTTPException(status_code=404, detail="Édition Touch introuvable.")
    return {"status": "ok", "edition": _public_admin_edition(edition)}


# ============================================================
# SAVE ADMINISTRATOR'S CORPUS CHOICES
# ============================================================

@router.put("/editions/{edition_id}/corpus")
def save_monthly_touch_corpus(
    edition_id: str,
    payload: TouchEditionCorpusRequest,
):
    try:
        edition = update_touch_edition_corpus(
            edition_id=edition_id,
            selected_content_ids=payload.selected_content_ids,
            dismissed_content_ids=payload.dismissed_content_ids,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if edition is None:
        raise HTTPException(status_code=404, detail="Édition Touch introuvable.")
    return {"status": "ok", "edition": _public_admin_edition(edition)}


# ============================================================
# LINK MONTHLY EDITION TO SAVED REPORT
# ============================================================

class TouchEditionReportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    report_id: str = Field(min_length=1)


@router.post("/editions/{edition_id}/report")
def link_monthly_touch_report(
    edition_id: str,
    payload: TouchEditionReportRequest,
):
    try:
        edition = link_touch_edition_report(
            edition_id=edition_id,
            report_id=payload.report_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if edition is None:
        raise HTTPException(status_code=404, detail="Édition Touch introuvable.")
    return {"status": "ok", "edition": _public_admin_edition(edition)}

@router.post("/reports/{report_id}/archive")
def archive_editorial_report(report_id: str):
    if not set_touch_report_archived(report_id, True):
        raise HTTPException(status_code=404, detail="Rapport Touch introuvable.")
    return {"status": "ok", "report_id": report_id}


@router.post("/reports/{report_id}/restore")
def restore_editorial_report(report_id: str):
    if not set_touch_report_archived(report_id, False):
        raise HTTPException(status_code=404, detail="Rapport Touch introuvable.")
    return {"status": "ok", "report_id": report_id}


@router.post("/editions/{edition_id}/reopen")
def reopen_monthly_touch_edition(edition_id: str):
    try:
        edition = reopen_touch_edition(edition_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if edition is None:
        raise HTTPException(status_code=404, detail="Édition Touch introuvable.")
    return {"status": "ok", "edition": _public_admin_edition(edition)}

# ============================================================
# DELETE MONTHLY EDITION AND LINKED REPORT
# ============================================================

@router.delete("/editions/{edition_id}")
def delete_monthly_touch_edition(
    edition_id: str,
):
    try:
        deleted = delete_touch_edition(
            edition_id=edition_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Erreur lors de la réinitialisation "
                f"de l’édition Touch : {exc}"
            ),
        ) from exc

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Édition Touch introuvable.",
        )

    return {
        "status": "ok",
        "edition_id": edition_id,
    }

# ============================================================
# KNOWLEDGE PUBLIC FRONT — PUBLISHED TOUCH REPORTS
# ============================================================

from fastapi import Request
from utils.auth import get_user_id_from_request
from core.user.user_service import get_user_by_id
from core.touch.library_models import LibraryFilters, LibrarySearchRequest
from core.touch.library_service import (
    browse_reports, library_filters, published_report, search_reports,
    set_report_published,
)


def _require_library_user(request: Request) -> dict:
    user_id = get_user_id_from_request(request)
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def _require_library_admin(request: Request) -> None:
    # Use the existing admin session convention, not the public user header.
    if request.cookies.get("ratecard_admin_session") != "ok":
        raise HTTPException(status_code=401, detail="Admin session required")


@router.get("/library/filters")
def get_report_library_filters(request: Request):
    _require_library_user(request)
    return {"status": "ok", "filters": library_filters()}


@router.get("/library/reports")
def list_published_touch_reports(
    request: Request,
    query: str = Query(default="", max_length=500),
    expert_id: str | None = None,
    month: str | None = Query(default=None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    output_language: Literal["fr", "en"] | None = None,
    limit: int = Query(default=20, ge=1, le=40),
    offset: int = Query(default=0, ge=0),
):
    _require_library_user(request)
    return {"status": "ok", **browse_reports(
        query=query, filters=LibraryFilters(expert_id=expert_id, month=month,
                                          output_language=output_language),
        limit=limit, offset=offset,
    )}


@router.get("/library/reports/{report_id}")
def get_published_touch_report(report_id: str, request: Request):
    _require_library_user(request)
    report = published_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Published report not found")
    # Public reader needs no internal corpus contribution or version lineage.
    return {"status": "ok", "report": {
        key: report[key] for key in (
            "report_id", "subject", "objective", "expert_id", "period_start",
            "period_end", "output_language", "created_at", "published_at",
            "sources", "notebook",
        )
    }}


@router.post("/library/search")
def search_published_touch_reports(payload: LibrarySearchRequest, request: Request):
    _require_library_user(request)
    try:
        return {"status": "ok", "search": search_reports(payload)}
    except Exception:
        import logging
        logging.getLogger(__name__).exception("Touch report library search failed")
        raise HTTPException(status_code=503, detail=(
            "Report discovery is temporarily unavailable. Use the catalogue search."
        ))


@router.post("/reports/{report_id}/publish")
def publish_touch_report(report_id: str, request: Request):
    _require_library_admin(request)
    try:
        updated = set_report_published(report_id, True)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not updated:
        raise HTTPException(status_code=404, detail="Touch report not found")
    return {"status": "ok", "report_id": report_id}


@router.post("/reports/{report_id}/unpublish")
def unpublish_touch_report(report_id: str, request: Request):
    _require_library_admin(request)
    if not set_report_published(report_id, False):
        raise HTTPException(status_code=404, detail="Touch report not found")
    return {"status": "ok", "report_id": report_id}
