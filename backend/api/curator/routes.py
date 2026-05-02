from fastapi import APIRouter, HTTPException, Query, Request
from typing import List, Dict, Optional

# ============================================================
# CORE CONTENT SERVICES
# ============================================================

from core.curator.service import (
    search,
    latest,
    get_item_curator,
    get_item_detail,
    get_content_stats,
)

# ============================================================
# 🔢 NUMBERS SERVICES (V1)
# ============================================================

from core.curator.numbers_service import (
    search_curator_numbers,
    latest_curator_numbers,
)

from core.curator.concept_service import get_concepts

# 🔐 AUTH
from utils.auth import get_user_id_from_request

router = APIRouter()


# ============================================================
# AUTH HELPER
# ============================================================

def require_user(request: Request) -> str:
    user_id = get_user_id_from_request(request)

    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return user_id


# ============================================================
# 🔍 SEARCH CONTENT
# ============================================================

@router.get("/search")
def search_route(
    request: Request,
    q: str = Query(...),
    limit: int = Query(20),
    offset: int = Query(0),
    type: Optional[str] = Query(None),
    universe_id: Optional[str] = Query(None),
):
    try:
        user_id = require_user(request)

        items = search(
            q=q,
            limit=limit,
            offset=offset,
            user_id=user_id,
            universe_id=universe_id,
        )

        return {"items": items, "count": len(items)}

    except Exception as e:
        print(f"❌ Search error: {e}")
        raise HTTPException(status_code=500, detail="Internal error")


# ============================================================
# 🆕 SEARCH NUMBERS (🔥 CORE V1)
# ============================================================

@router.get("/numbers")
def search_numbers_route(
    request: Request,
    q: Optional[str] = Query(None),
    limit: int = Query(50),
    offset: int = Query(0),
    universe_id: Optional[str] = Query(None),
    concept_ids: Optional[List[str]] = Query(None),  # 🔥 NEW
):
    try:
        user_id = require_user(request)

        items = search_curator_numbers(
            query=q,
            limit=limit,
            offset=offset,
            user_id=user_id,
            universe_id=universe_id,
            concept_ids=concept_ids,  # 🔥 injecté
        )

        return {"items": items, "count": len(items)}

    except Exception as e:
        print(f"❌ Numbers search error: {e}")
        raise HTTPException(status_code=500, detail="Internal error")

@router.get("/concepts")
def get_concepts_route(request: Request):
    try:
        user_id = require_user(request)

        items = get_concepts(user_id)

        return {"items": items}

    except Exception as e:
        print(f"❌ Concepts error: {e}")
        raise HTTPException(status_code=500, detail="Internal error")

# ============================================================
# 🆕 LATEST NUMBERS
# ============================================================

@router.get("/numbers/latest")
def latest_numbers_route(
    request: Request,
    limit: int = Query(50),
    offset: int = Query(0),
    universe_id: Optional[str] = Query(None),
    concept_ids: Optional[List[str]] = Query(None),  # 🔥 NEW
):
    try:
        user_id = require_user(request)

        items = latest_curator_numbers(
            limit=limit,
            offset=offset,
            user_id=user_id,
            universe_id=universe_id,
            concept_ids=concept_ids,
        )

        return {"items": items, "count": len(items)}

    except Exception as e:
        print(f"❌ Latest numbers error: {e}")
        raise HTTPException(status_code=500, detail="Internal error")




# ============================================================
# 🆕 NUMBERS FROM CONTENT (DRAWER)
# ============================================================

@router.get("/numbers/by-content/{content_id}")
def numbers_by_content_route(
    request: Request,
    content_id: str,
):
    try:
        _ = require_user(request)

        from core.curator.numbers_service import search_curator_numbers

        # 🔥 filtrage direct SQL (clean)
        items = search_curator_numbers(
            query=None,
            limit=200,
            offset=0,
            user_id=None,  # optionnel ici
            universe_id=None,
            concept_ids=None,
        )

        # 🔥 filtre propre
        items = [i for i in items if i.get("ID_CONTENT") == content_id]

        return {"items": items, "count": len(items)}

    except Exception as e:
        print(f"❌ Numbers by content error: {e}")
        raise HTTPException(status_code=500, detail="Internal error")


# ============================================================
# 🆕 INSIGHT NUMBERS (V1)
# ============================================================

@router.post("/numbers/insight")
def numbers_insight_route(
    request: Request,
    payload: dict,
):
    try:
        _ = require_user(request)

        ids = payload.get("ids", [])

        from core.numbers.backlog_service import generate_backlog_insight

        insight = generate_backlog_insight(ids)

        return {"insight": insight}

    except Exception as e:
        print(f"❌ Numbers insight error: {e}")
        raise HTTPException(status_code=500, detail="Internal error")


# ============================================================
# 🆕 LATEST CONTENT
# ============================================================

@router.get("/latest")
def latest_route(
    request: Request,
    limit: int = Query(20),
    offset: int = Query(0),
    type: Optional[str] = Query(None),
    universe_id: Optional[str] = Query(None),
):
    try:
        user_id = require_user(request)

        items = latest(
            limit=limit,
            offset=offset,
            user_id=user_id,
            universe_id=universe_id,
        )

        return {"items": items, "count": len(items)}

    except Exception as e:
        print(f"❌ Latest error: {e}")
        raise HTTPException(status_code=500, detail="Internal error")


# ============================================================
# 📊 STATS
# ============================================================

@router.get("/stats")
def stats_route(request: Request):
    try:
        _ = require_user(request)

        stats = get_content_stats()
        return {"status": "ok", "stats": stats}

    except Exception as e:
        print(f"❌ Stats error: {e}")
        raise HTTPException(status_code=500, detail="Internal error")


# ============================================================
# 📄 ITEM
# ============================================================

@router.get("/item/{item_id}")
def read_item(request: Request, item_id: str):
    try:
        user_id = require_user(request)

        item = get_item_curator(item_id, user_id=user_id)

        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        return item

    except Exception as e:
        print(f"❌ Item error: {e}")
        raise HTTPException(status_code=500, detail="Internal error")


# ============================================================
# 📄 DETAIL
# ============================================================

@router.get("/item/{item_id}/detail")
def read_item_detail(request: Request, item_id: str):
    try:
        user_id = require_user(request)

        item = get_item_detail(item_id, user_id=user_id)

        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        return item

    except Exception as e:
        print(f"❌ Detail error: {e}")
        raise HTTPException(status_code=500, detail="Internal error")
