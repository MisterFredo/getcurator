# backend/api/watch/routes.py

from fastapi import (
    APIRouter,
)

from core.watch.watch_service import (
    latest,
    search,
    get_watch_content,
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
def latest_route(
    user_id: str,
    limit: int = 20,
    offset: int = 0,
    universe_id: str | None = None,
    company_id: str | None = None,
    solution_id: str | None = None,
    topic_id: str | None = None,
):
    return latest(
        user_id=user_id,
        limit=limit,
        offset=offset,
        universe_id=universe_id,
        company_id=company_id,
        solution_id=solution_id,
        topic_id=topic_id,
    )

# ============================================================
# SEARCH
# ============================================================

@router.get("/search")
def search_route(

    user_id: str,

    query: str,

    limit: int = 20,

    offset: int = 0,

    universe_id: str | None = None,

):

    return search(

        user_id=user_id,

        query=query,

        limit=limit,

        offset=offset,

        universe_id=universe_id,

    )


# ============================================================
# CONTENT (DRAWER)
# ============================================================

@router.get("/content/{content_id}")
def content_route(

    content_id: str,

    user_id: str | None = None,

):

    return get_watch_content(

        content_id=content_id,

        user_id=user_id,

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
