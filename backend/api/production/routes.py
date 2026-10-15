import logging

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
)

from fastapi import (
    File,
    UploadFile,
)

from openai import (
    APIConnectionError,
    APIStatusError,
)

from starlette.concurrency import (
    run_in_threadpool,
)

from core.production.pdf_test_service import (
    MAX_TOTAL_BYTES,
    get_pdf_test,
    start_pdf_test,
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

from core.production.plan_service import (
    generate_production_plan,
)

from core.production.plan_repository import (
    get_production_plan,
    list_production_plans,
    save_production_plan,
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
# PDF COMPARISON TEST
# ============================================================

@router.post(
    "/pdf-test/jobs",
    status_code=202,
)
async def create_pdf_test_job(
    sources: list[UploadFile] = File(...),
    prototype: UploadFile = File(...),
):
    uploads = [
        *sources,
        prototype,
    ]

    try:
        if len(sources) != 3:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Sélectionne exactement "
                    "trois rapports sources."
                ),
            )

        documents = []
        remaining = MAX_TOTAL_BYTES

        for upload in uploads:
            data = await upload.read(
                remaining + 1
            )

            if len(data) > remaining:
                raise HTTPException(
                    status_code=413,
                    detail=(
                        "Les quatre PDF doivent "
                        "totaliser au maximum 20 Mo."
                    ),
                )

            remaining -= len(data)

            documents.append((
                upload.filename or "document.pdf",
                data,
            ))

        job = await run_in_threadpool(
            start_pdf_test,
            documents,
        )

        return {
            "status": "ok",
            "job": job,
        }

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except APIStatusError as exc:
        logger.exception(
            "PDF test API rejection"
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "OpenAI a refusé la demande "
                f"(HTTP {exc.status_code}). "
                "Vérifier le modèle, les droits "
                "du projet et les logs backend."
            ),
        ) from exc

    except APIConnectionError as exc:
        logger.exception(
            "PDF test connection failure"
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "La connexion à OpenAI a échoué. "
                "L'acceptation de la demande "
                "n'est pas confirmée. Ne pas "
                "relancer automatiquement."
            ),
        ) from exc

    except Exception as exc:
        logger.exception(
            "PDF test creation failed"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Impossible de démarrer "
                "l'essai PDF. Consulter "
                "les logs avant de relancer."
            ),
        ) from exc

    finally:
        for upload in uploads:
            await upload.close()


@router.get(
    "/pdf-test/jobs/{response_id}",
)
def read_pdf_test_job(
    response_id: str,
):
    try:
        job = get_pdf_test(
            response_id=response_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except APIStatusError as exc:
        logger.exception(
            "PDF test retrieval rejected: %s",
            response_id,
        )

        raise HTTPException(
            status_code=(
                404
                if exc.status_code == 404
                else 502
            ),
            detail=(
                "Génération introuvable "
                "ou indisponible chez OpenAI."
            ),
        ) from exc

    except Exception as exc:
        logger.exception(
            "PDF test retrieval failed: %s",
            response_id,
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "Impossible de récupérer "
                "la génération. Son traitement "
                "peut toujours être en cours."
            ),
        ) from exc

    return {
        "status": "ok",
        "job": job,
    }


# ============================================================
# CREATE PRODUCTION AND FREEZE ITS CORPUS
# ============================================================

@router.post(
    "/",
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

@router.get("/")
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


# ============================================================
# GENERATE AND SAVE A NEW PLAN
# ============================================================

@router.post(
    "/{production_id}/plan",
    status_code=201,
)
def generate_editorial_plan(
    production_id: str,
):
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
            detail="Production introuvable.",
        )

    if production["status"] not in {
        "CORPUS_PREPARED",
        "PLAN_TO_REVIEW",
    }:
        raise HTTPException(
            status_code=409,
            detail=(
                "La production ne permet pas "
                "une nouvelle génération du plan "
                "dans son état actuel."
            ),
        )

    try:
        snapshot = generate_production_plan(
            production_id=production_id,
        )

        saved_plan = save_production_plan(
            snapshot=snapshot,
        )

    except ValueError as exc:
        logger.exception(
            "Production plan rejected: %s",
            production_id,
        )

        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception(
            "Production plan generation "
            "or saving failed: %s",
            production_id,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "La génération ou "
                "l'enregistrement du plan "
                "n'a pas abouti. Consultez "
                "l'historique avant de relancer."
            ),
        ) from exc

    return {
        "status": "ok",
        "plan": saved_plan,
    }


# ============================================================
# READ LATEST OR SPECIFIC PLAN
# ============================================================

@router.get("/{production_id}/plan")
def read_editorial_plan(
    production_id: str,
    version: int | None = Query(
        default=None,
        ge=1,
    ),
):
    try:
        plan = get_production_plan(
            production_id=production_id,
            version=version,
        )

    except Exception as exc:
        logger.exception(
            "Production plan loading failed: %s",
            production_id,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Impossible de charger le plan."
            ),
        ) from exc

    if plan is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Aucun plan trouvé "
                "pour cette production "
                "et cette version."
            ),
        )

    return {
        "status": "ok",
        "plan": plan,
    }


# ============================================================
# LIST PLAN HISTORY
# ============================================================

@router.get("/{production_id}/plans")
def browse_editorial_plan_versions(
    production_id: str,
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
        plans = list_production_plans(
            production_id=production_id,
            limit=limit,
            offset=offset,
        )

    except Exception as exc:
        logger.exception(
            "Production plan history failed: %s",
            production_id,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Impossible de charger "
                "l'historique des plans."
            ),
        ) from exc

    return {
        "status": "ok",
        "plans": plans,
    }
