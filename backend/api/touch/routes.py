from fastapi import (
    APIRouter,
    HTTPException,
)
from typing import Literal

from pydantic import BaseModel

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
def list_editorial_reports():
    return {
        "status": "ok",
        "reports": list_touch_reports(),
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
