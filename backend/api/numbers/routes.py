from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from api.numbers.models import NumberInput

from core.numbers.service import (
    create_number,
    list_numbers,
    delete_number,
    get_numbers_from_content,
    check_number_coherence,
    get_number_types,
    search_numbers_service,
    get_numbers_feed_service,
    get_numbers_for_entity,
)

from core.numbers.insight_service import (
    generate_numbers_insight,
    get_numbers_by_ids,
)

from core.numbers.transformer_service import (
    preview_content_numbers_dict,
    transform_and_save_content_numbers,
)

from core.knowledge.number_builder_service import (
    build_number_knowledge,
)

from core.knowledge.number_orchestrator_service import (
    continue_number_knowledge,
    get_number_knowledge_status,
)

from core.numbers.backfill_service import (
    get_number_backfill_status,
    run_number_backfill_batch,
)

from core.numbers.moderation_service import (
    apply_number_decisions,
    list_number_observations,
)

from core.numbers.retrieval_service import (
    search_validated_numbers,
)

from core.numbers.content_service import (
    get_validated_numbers_for_content,
)

router = APIRouter()


# ============================================================
# CREATE
# ============================================================

@router.post("/")
def create_route(payload: NumberInput):

    try:
        result = create_number(payload)

        return {
            "status": "ok",
            "id_number": result["id_number"],
            "quality": result.get("quality"),
        }

    except Exception as e:
        raise HTTPException(400, f"Erreur création number : {e}")


# ============================================================
# LIST
# ============================================================

@router.get("/")
def list_route(limit: int = 100):

    try:
        items = list_numbers(limit=limit)

        return {
            "status": "ok",
            "items": items,
        }

    except Exception as e:
        raise HTTPException(400, f"Erreur list numbers : {e}")


# ============================================================
# DELETE
# ============================================================

@router.delete("/{id_number}")
def delete_route(id_number: str):

    try:
        delete_number(id_number)

        return {
            "status": "ok",
            "deleted": True,
        }

    except Exception as e:
        raise HTTPException(400, f"Erreur suppression number : {e}")

# ============================================================
# TRANSFORM PREVIEW
# ============================================================

@router.post("/transform-preview/{id_content}")
def transform_preview_route(
    id_content: str,
):

    try:

        result = preview_content_numbers_dict(
            id_content=id_content,
        )

        return {
            "status": "ok",
            "result": result,
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=(
                "Erreur transformation Numbers : "
                f"{e}"
            ),
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                "Erreur interne transformation "
                f"Numbers : {e}"
            ),
        )

# ============================================================
# TRANSFORM AND SAVE
# ============================================================

@router.post("/transform/{id_content}")
def transform_and_save_route(
    id_content: str,
):

    try:

        result = transform_and_save_content_numbers(
            id_content=id_content,
        )

        return {
            "status": "ok",
            "result": result,
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=(
                "Erreur transformation Numbers : "
                f"{e}"
            ),
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                "Erreur sauvegarde Numbers : "
                f"{e}"
            ),
        )

# ============================================================
# NUMBER OBSERVATIONS
# ============================================================

@router.get("/observations")
def list_number_observations_route(
    status: Optional[str] = None,
    query: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    limit: int = Query(
        100,
        ge=1,
        le=500,
    ),
    offset: int = Query(
        0,
        ge=0,
    ),
):

    try:

        result = list_number_observations(
            status=status,
            query=query,
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit,
            offset=offset,
        )

        return {
            "status": "ok",
            **result,
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=(
                "Erreur observations Numbers : "
                f"{e}"
            ),
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                "Erreur interne observations "
                f"Numbers : {e}"
            ),
        )


# ============================================================
# BULK NUMBER DECISIONS
# ============================================================

@router.post("/observations/decisions")
def apply_number_decisions_route(
    payload: dict,
):

    try:

        result = apply_number_decisions(
            ids=payload.get(
                "ids",
                [],
            ),
            decision=payload.get(
                "decision",
                "",
            ),
            reason=payload.get(
                "reason",
            ),
            reviewed_by=payload.get(
                "reviewed_by",
            ),
        )

        return {
            "status": "ok",
            "result": result,
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=(
                "Erreur modération Numbers : "
                f"{e}"
            ),
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                "Erreur interne modération "
                f"Numbers : {e}"
            ),
        )


# ============================================================
# PUBLIC VALIDATED NUMBERS
# ============================================================

@router.get("/public")
def public_numbers_route(
    query: Optional[str] = None,
    user_id: Optional[str] = None,
    universe_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    metric_type: Optional[str] = None,
    zone: Optional[str] = None,
    period: Optional[str] = None,
    limit: int = Query(
        50,
        ge=1,
        le=200,
    ),
    offset: int = Query(
        0,
        ge=0,
    ),
):

    try:

        result = search_validated_numbers(
            query=query,
            user_id=user_id,
            universe_id=universe_id,
            entity_type=entity_type,
            entity_id=entity_id,
            metric_type=metric_type,
            zone=zone,
            period=period,
            limit=limit,
            offset=offset,
        )

        return {
            "status": "ok",
            **result,
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=(
                "Erreur recherche Numbers : "
                f"{e}"
            ),
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                "Erreur interne recherche "
                f"Numbers : {e}"
            ),
        )

# ============================================================
# VALIDATED NUMBERS FOR CONTENT
# ============================================================

@router.get(
    "/content/{id_content}"
)
def validated_numbers_for_content_route(
    id_content: str,
):

    try:

        items = (
            get_validated_numbers_for_content(
                id_content=id_content,
            )
        )

        return {
            "status": "ok",
            "id_content": id_content,
            "count": len(items),
            "items": items,
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                "Erreur interne Numbers "
                f"du contenu : {e}"
            ),
        )


# ============================================================
# NUMBERS BACKFILL STATUS
# ============================================================

@router.get("/backfill/status")
def number_backfill_status_route():

    try:

        return {
            "status": "ok",
            "result": (
                get_number_backfill_status()
            ),
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                "Erreur monitoring backfill "
                f"Numbers : {e}"
            ),
        )

# ============================================================
# NUMBERS BACKFILL
# ============================================================

@router.post("/backfill")
def backfill_numbers_route(
    limit: int = Query(
        5,
        ge=1,
        le=10,
    ),
    retry_failed: bool = Query(
        False,
    ),
):

    try:

        result = run_number_backfill_batch(
            limit=limit,
            retry_failed=retry_failed,
        )

        return {
            "status": "ok",
            "result": result,
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=(
                "Erreur backfill Numbers : "
                f"{e}"
            ),
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                "Erreur interne backfill "
                f"Numbers : {e}"
            ),
        )

# ============================================================
# NUMBERS KNOWLEDGE STATUS
# ============================================================

@router.get("/knowledge/status")
def number_knowledge_status_route():

    try:

        return {
            "status": "ok",
            "result": (
                get_number_knowledge_status()
            ),
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                "Erreur monitoring Numbers "
                f"Knowledge : {e}"
            ),
        )

# ============================================================
# CONTINUE NUMBERS KNOWLEDGE
# ============================================================

@router.post("/knowledge/continue")
def continue_number_knowledge_route(
    limit: int = Query(
        5,
        ge=1,
        le=10,
    ),
):

    try:

        result = continue_number_knowledge(
            limit=limit,
        )

        return {
            "status": "ok",
            "result": result,
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                "Erreur Continue Numbers "
                f"Knowledge : {e}"
            ),
        )

# ============================================================
# BUILD NUMBER KNOWLEDGE
# ============================================================

@router.post(
    "/knowledge/{entity_type}/{entity_id}"
)
def build_number_knowledge_route(
    entity_type: str,
    entity_id: str,
):

    try:

        result = build_number_knowledge(

            entity_type=entity_type,

            entity_id=entity_id,

        )

        return {
            "status": "ok",
            "result": result,
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=(
                "Erreur Knowledge Numbers : "
                f"{e}"
            ),
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                "Erreur interne Knowledge "
                f"Numbers : {e}"
            ),
        )

# ============================================================
# FROM CONTENT
# ============================================================

@router.get("/from-content/{id_content}")
def from_content_route(id_content: str):

    try:
        items = get_numbers_from_content(id_content)

        return {
            "status": "ok",
            "items": items,
        }

    except Exception as e:
        raise HTTPException(400, f"Erreur parsing content : {e}")


# ============================================================
# COHERENCE CHECK
# ============================================================

@router.post("/check-coherence")
def check_coherence_route(payload: dict):

    try:
        result = check_number_coherence(
            value=payload.get("value"),
            id_number_type=payload.get("id_number_type"),
            zone=payload.get("zone"),
            period=payload.get("period"),
            company_id=payload.get("company_id"),
            topic_id=payload.get("topic_id"),
            solution_id=payload.get("solution_id"),
        )

        return {
            "status": "ok",
            "result": result,
        }

    except Exception as e:
        raise HTTPException(400, f"Erreur coherence check : {e}")


# ============================================================
# TYPES
# ============================================================

@router.get("/types")
def get_types():

    try:
        items = get_number_types()
        return items

    except Exception as e:
        raise HTTPException(400, f"Erreur types numbers : {e}")


# ============================================================
# SEARCH
# ============================================================

@router.get("/search")
def search_numbers(
    id_number_type: Optional[str] = None,
    topic_id: Optional[str] = None,
    company_id: Optional[str] = None,
    solution_id: Optional[str] = None,
    limit: int = 200,
):

    items = search_numbers_service(
        id_number_type=id_number_type,
        topic_id=topic_id,
        company_id=company_id,
        solution_id=solution_id,
        limit=limit,
    )

    return {
        "status": "ok",
        "items": items,
    }


# ============================================================
# BY ENTITY
# ============================================================

@router.get("/entity")
def numbers_by_entity(
    entity_type: str,
    entity_id: str,
    limit: Optional[int] = None,
):

    try:
        items = get_numbers_for_entity(
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit,
        )

        return {
            "status": "ok",
            "items": items,
        }

    except Exception as e:
        raise HTTPException(400, f"Erreur numbers entity : {e}")


# ============================================================
# FEED (🔥 UNIVERSE ONLY — CLEAN)
# ============================================================

@router.get("/feed")
def get_numbers_feed(
    limit: int = 50,
    query: Optional[str] = None,
    universe_id: Optional[str] = Query(None),
):

    try:
        items = get_numbers_feed_service(
            limit=limit,
            query=query,
            universe_id=universe_id if universe_id else None,
        )

        return {
            "status": "ok",
            "items": items,
        }

    except Exception as e:
        raise HTTPException(400, f"Erreur numbers feed : {e}")


# ============================================================
# INSIGHT
# ============================================================

@router.post("/insight")
def numbers_insight(payload: dict):

    try:
        ids = payload.get("ids", [])

        insight = generate_numbers_insight(ids)

        return {
            "status": "ok",
            "insight": insight,
        }

    except Exception as e:
        raise HTTPException(400, f"Erreur numbers insight : {e}")
