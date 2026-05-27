# backend/api/digest/routes.py

from fastapi import (
    APIRouter,
    Query,
)

from core.digest.content_service import (
    get_digest_contents,
)

router = APIRouter()

# ============================================================
# MY FEED
# ============================================================

@router.get("/my-feed")
def digest_my_feed(
    user_id: str = Query(...),

    limit: int = Query(
        50
    ),
):

    result = get_digest_contents(
        user_id=user_id,

        limit=limit,
    )

    return {
        "status": "ok",

        "result": result,
    }
