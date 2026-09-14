from fastapi import (
    APIRouter,
    HTTPException,
)

from core.touch.search_models import (
    TouchResearchBrief,
)

from core.touch.search_service import (
    search_touch_contents,
)


router = APIRouter()


# ============================================================
# SEARCH
# ============================================================

@router.post("/search")
def search_touch(
    brief: TouchResearchBrief,
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
