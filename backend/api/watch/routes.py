# backend/api/watch/routes.py

from fastapi import APIRouter

from core.watch.watch_service import (
    latest,
    search,
    get_item,
    get_item_detail,
    add_to_workspace,
)

router = APIRouter()

# ============================================================
# LATEST
# ============================================================

@router.get("/latest")
def latest_route():
    return latest()


# ============================================================
# SEARCH
# ============================================================

@router.get("/search")
def search_route():
    return search()


# ============================================================
# ITEM
# ============================================================

@router.get("/{item_id}")
def item_route(
    item_id: str,
):
    return get_item(item_id)


# ============================================================
# DETAIL
# ============================================================

@router.get("/{item_id}/detail")
def detail_route(
    item_id: str,
):
    return get_item_detail(item_id)


# ============================================================
# WORKSPACE
# ============================================================

@router.post("/workspace")
def workspace_route():
    return add_to_workspace()
