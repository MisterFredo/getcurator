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

        return {

            "status":
                "ok",

            "search":
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
                "Erreur lors de la recherche "
                f"éditoriale Touch : {exc}"
            ),
        ) from exc
