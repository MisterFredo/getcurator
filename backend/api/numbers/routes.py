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
    get_raw_numbers,
    search_numbers_service,
    get_numbers_feed_service,
    get_numbers_for_entity,
)

from core.numbers.insight_service import (
    generate_numbers_insight,
    get_numbers_by_ids,
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
# RAW
# ============================================================

@router.get("/raw")
def raw_numbers(limit: int = 500):

    try:
        items = get_raw_numbers(limit=limit)

        return {
            "status": "ok",
            "items": items,
        }

    except Exception as e:
        raise HTTPException(400, f"Erreur raw numbers : {e}")


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
