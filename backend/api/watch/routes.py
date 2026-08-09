# backend/api/watch/routes.py

from fastapi import APIRouter

from core.watch.watch_service import (
    latest,
    search,
    get_content,
)

from core.watch.workspace_service import (
    add_content,
    remove_content,
)

router = APIRouter()

# ============================================================
# WATCH
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
# CONTENT (DRAWER)
# ============================================================

@router.get("/content/{content_id}")
def content_route(
    content_id: str,
):
    return get_content(
        content_id,
    )


# ============================================================
# WORKSPACE
# ============================================================

@router.post("/workspace/add")
def add_workspace_route():
    return add_content()


@router.delete("/workspace/{content_id}")
def remove_workspace_route(
    content_id: str,
):
    return remove_content(
        content_id,
    )
