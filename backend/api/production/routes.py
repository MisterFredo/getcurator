import logging

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
)

from core.production.corpus_service import (
    prepare_production_corpus,
)

from core.production.models import (
    ProductionPrepareRequest,
)

from core.production.repository import (
    get_production,
    list_productions,
    save_prepared_production,
)

from core.user.user_service import (
    get_user_by_id,
)

from utils.auth import (
    get_user_id_from_request,
)


logger = logging.getLogger(__name__)


# ============================================================
# ADMIN ACCESS
# ============================================================

def _require_production_admin(
    request: Request,
) -> None:
    user_id = get_user_id_from_request(
        request
    )

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    user = get_user_by_id(
        user_id
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    role = str(
        user.get("ROLE") or ""
    ).strip().lower()

    if role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required",
        )


router = APIRouter(
    dependencies=[
        Depends(
            _require_production_admin
        ),
    ],
)


# ============================================================
# CREATE PRODUCTION AND FREEZE ITS CORPUS
# ============================================================

@router.post(
    "",
    status_code=201,
)
def create_production(
    payload: ProductionPrepareRequest,
):
    try:
        corpus = (
            prepare_production_corpus(
                request=payload,
            )
        )

        production = (
            save_prepared_production(
                corpus=corpus,
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception(
            "Production corpus preparation failed"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Impossible de préparer "
                "la production."
            ),
        ) from exc

    return {
        "status": "ok",
        "production": production,
    }


# ============================================================
# LIST PRODUCTIONS
# ============================================================

@router.get("")
def browse_productions(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
):
    try:
        productions = (
            list_productions(
                limit=limit,
                offset=offset,
            )
        )

    except Exception as exc:
        logger.exception(
            "Production listing failed"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Impossible de charger "
                "les productions."
            ),
        ) from exc

    return {
        "status": "ok",
        "productions": productions,
    }


# ============================================================
# GET SAVED PRODUCTION
# ============================================================

@router.get("/{production_id}")
def read_production(
    production_id: str,
):
    production_id = (
        production_id.strip()
    )

    if not production_id:
        raise HTTPException(
            status_code=400,
            detail=(
                "Identifiant de production vide."
            ),
        )

    try:
        production = get_production(
            production_id=production_id,
        )

    except Exception as exc:
        logger.exception(
            "Production loading failed: %s",
            production_id,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Impossible de charger "
                "la production."
            ),
        ) from exc

    if production is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Production introuvable."
            ),
        )

    return {
        "status": "ok",
        "production": production,
    }
