from fastapi import (
    APIRouter,
    HTTPException,
)
from typing import Literal

from core.touch.search_models import (
    TouchResearchBrief,
)

from core.touch.search_service import (
    search_touch_contents,
)

from core.touch.generation_models import (
    TouchGenerationRequest,
)

from core.touch.generation_service import (
    generate_touch_one_pager,
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
