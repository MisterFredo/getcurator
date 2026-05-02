from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from api.numbers.models import (
    NumberInput,
    NumberBacklogUpdate,
)

# ============================================================
# V2 SERVICES (OFFICIAL)
# ============================================================

from core.numbers.create import create_number
from core.numbers.service import (
    list_numbers,
    delete_number,
    delete_numbers_by_source,
    get_number_types,
)
from core.numbers.parsing import get_numbers_from_content
from core.numbers.search import (
    search_numbers_service,
    get_numbers_feed_service,
    get_numbers_for_entity,
    get_numbers_admin_service,
)
from core.numbers.insight_service import generate_numbers_insight

# ============================================================
# V1 SERVICES (BACKLOG) — 🔥 À CRÉER
# ============================================================

from core.numbers.backlog_service import (
    get_backlog_feed,
    get_backlog_admin,
    update_backlog_decision,
    generate_backlog_insight,
)

router = APIRouter()

# ============================================================
# CREATE (V2)
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
# ADMIN V2 (OFFICIAL)
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

        return {"status": "ok", "items": items}

    except Exception as e:
        raise HTTPException(400, f"Erreur admin numbers : {e}")

# ============================================================
# ADMIN V1 (BACKLOG)
# ============================================================

@router.get("/backlog")
def get_numbers_backlog(
    limit: int = 200,
    offset: int = 0,
    query: Optional[str] = None,
):
    try:
        items = get_backlog_admin(
            limit=limit,
            offset=offset,
            query=query,
        )

        return {"status": "ok", "items": items}

    except Exception as e:
        raise HTTPException(400, f"Erreur backlog numbers : {e}")

@router.post("/backlog/update/{id_backlog}")
def update_backlog(id_backlog: str, payload: NumberBacklogUpdate):
    try:
        update_backlog_decision(id_backlog, payload.decision)

        return {"status": "ok"}

    except Exception as e:
        raise HTTPException(400, f"Erreur update backlog : {e}")

# ============================================================
# DELETE (V2)
# ============================================================

@router.delete("/{id_number}")
def delete_route(id_number: str):
    try:
        delete_number(id_number)

        return {"status": "ok", "deleted": True}

    except Exception as e:
        raise HTTPException(400, f"Erreur suppression number : {e}")

# ============================================================
# CURATOR — FEED V2 (OFFICIAL)
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

        return {"status": "ok", "items": items}

    except Exception as e:
        raise HTTPException(400, f"Erreur numbers feed : {e}")

# ============================================================
# CURATOR — FEED V1 (BACKLOG)
# ============================================================

@router.get("/feed/backlog")
def get_numbers_feed_backlog(
    limit: int = 50,
):
    try:
        items = get_backlog_feed(limit=limit)

        return {"status": "ok", "items": items}

    except Exception as e:
        raise HTTPException(400, f"Erreur backlog feed : {e}")

# ============================================================
# CURATOR — ENTITY (V2 ONLY)
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

        return {"status": "ok", "items": items}

    except Exception as e:
        raise HTTPException(400, f"Erreur numbers entity : {e}")

# ============================================================
# INSIGHT V2
# ============================================================

@router.post("/insight")
def numbers_insight(payload: dict):
    try:
        ids = payload.get("ids", [])
        insight = generate_numbers_insight(ids)

        return {"status": "ok", "insight": insight}

    except Exception as e:
        raise HTTPException(400, f"Erreur numbers insight : {e}")

# ============================================================
# INSIGHT V1 (BACKLOG)
# ============================================================

@router.post("/backlog/insight")
def numbers_backlog_insight(payload: dict):
    try:
        ids = payload.get("ids", [])
        insight = generate_backlog_insight(ids)

        return {"status": "ok", "insight": insight}

    except Exception as e:
        raise HTTPException(400, f"Erreur backlog insight : {e}")
