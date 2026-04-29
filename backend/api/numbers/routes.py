from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from api.numbers.models import NumberInput

# ============================================================
# CORE SERVICES
# ============================================================

from core.numbers.create import create_number
from core.numbers.service import list_numbers, delete_number
from core.numbers.parsing import get_numbers_from_content
from core.numbers.search import (
    search_numbers_service,
    get_numbers_feed_service,
    get_numbers_for_entity,
    get_numbers_admin_service,  # 🔥 FIX
)
from core.numbers.service import get_number_types
from core.numbers.insight_service import generate_numbers_insight

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
# ADMIN (🔥 CONTROL PANEL PRINCIPAL)
# ============================================================

@router.get("/admin")
def get_numbers_admin(
    limit: int = 200,
    offset: int = 0,
    query: Optional[str] = None,
    type_id: Optional[str] = None,
    source_id: Optional[str] = None,
):

    try:
        items = get_numbers_admin_service(
            limit=limit,
            offset=offset,
            query=query,
            type_id=type_id,
            source_id=source_id,
        )

        return {
            "status": "ok",
            "items": items,
        }

    except Exception as e:
        raise HTTPException(400, f"Erreur admin numbers : {e}")


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
            "id_number": id_number,
        }

    except Exception as e:
        raise HTTPException(400, f"Erreur suppression number : {e}")

@router.delete("/by-source/{source_id}")
def delete_numbers_by_source(source_id: str):


# ============================================================
# FROM CONTENT (DEBUG / ANALYSE)
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
# TYPES
# ============================================================

@router.get("/types")
def get_types():

    try:
        return get_number_types()

    except Exception as e:
        raise HTTPException(400, f"Erreur types numbers : {e}")


# ============================================================
# SEARCH (ADMIN SEARCH SIMPLE)
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
# CURATOR — FEED
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
            universe_id=universe_id,
        )

        return {
            "status": "ok",
            "items": items,
        }

    except Exception as e:
        raise HTTPException(400, f"Erreur numbers feed : {e}")


# ============================================================
# CURATOR — ENTITY
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
# CURATOR — INSIGHT
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
