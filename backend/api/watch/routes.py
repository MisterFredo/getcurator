# backend/api/watch/routes.py

from time import perf_counter

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

    period_start: str | None = None,

    period_end: str | None = None,

    universe_id: str | None = None,

    company_id: str | None = None,

    solution_id: str | None = None,

    topic_id: str | None = None,

):

    t0 = perf_counter()

    print(
        "⏱️ WATCH /latest START",
        {
            "user_id": user_id,
            "limit": limit,
            "offset": offset,
            "period_start": period_start,
            "period_end": period_end,
            "universe_id": universe_id,
            "company_id": company_id,
            "solution_id": solution_id,
            "topic_id": topic_id,
        },
    )

    result = latest(

        user_id=user_id,

        limit=limit,

        offset=offset,

        period_start=period_start,

        period_end=period_end,

        universe_id=universe_id,

        company_id=company_id,

        solution_id=solution_id,

        topic_id=topic_id,

    )

    print(
        "⏱️ WATCH /latest TOTAL:",
        round(
            perf_counter() - t0,
            3,
        ),
        "s",
    )

    return result


# ============================================================
# SEARCH
# ============================================================

@router.get("/search")
def search_route(

    user_id: str,

    query: str,

    limit: int = 20,

    offset: int = 0,

    period_start: str | None = None,

    period_end: str | None = None,

    universe_id: str | None = None,

    company_id: str | None = None,

    solution_id: str | None = None,

    topic_id: str | None = None,

):

    t0 = perf_counter()

    print(
        "⏱️ WATCH /search START",
        {
            "user_id": user_id,
            "query": query,
            "limit": limit,
            "offset": offset,
            "period_start": period_start,
            "period_end": period_end,
            "universe_id": universe_id,
            "company_id": company_id,
            "solution_id": solution_id,
            "topic_id": topic_id,
        },
    )

    result = search(

        user_id=user_id,

        query=query,

        limit=limit,

        offset=offset,

        period_start=period_start,

        period_end=period_end,

        universe_id=universe_id,

        company_id=company_id,

        solution_id=solution_id,

        topic_id=topic_id,

    )

    print(
        "⏱️ WATCH /search TOTAL:",
        round(
            perf_counter() - t0,
            3,
        ),
        "s",
    )

    return result


# ============================================================
# CONTENT (DRAWER)
# ============================================================

@router.get("/content/{content_id}")
def content_route(

    content_id: str,

    user_id: str | None = None,

):

    t0 = perf_counter()

    result = get_watch_content(

        content_id=content_id,

        user_id=user_id,

    )

    print(
        "⏱️ WATCH /content TOTAL:",
        round(
            perf_counter() - t0,
            3,
        ),
        "s",
    )

    return result


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
