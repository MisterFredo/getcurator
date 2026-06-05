from fastapi import (
    APIRouter,
)

from core.newsletter.service import (
    search_newsletter_content,
)

router = APIRouter()

# ============================================================
# NEWSLETTER SEARCH
# ============================================================

@router.post("/search")
def newsletter_search(payload: dict):

    period = payload.get(
        "period",
        "total",
    )

    if period not in (
        "total",
        "30d",
        "7d",
    ):
        period = "total"

    result = search_newsletter_content(
        topics=payload.get("topics"),
        companies=payload.get("companies"),
        news_types=payload.get("news_types"),
        limit=payload.get("limit", 20),
        cursor=payload.get("cursor"),
        period=period,
        date_from=payload.get("date_from"),
        date_to=payload.get("date_to"),
    )

    return {
        "status": "ok",
        "result": result,
    }
