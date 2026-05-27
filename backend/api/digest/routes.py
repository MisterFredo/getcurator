from fastapi import APIRouter

from core.digest.content_service import (
    search_digest_content,
)

router = APIRouter()


@router.post("/search")
def digest_search(payload: dict):

    result = search_digest_content(
        query=payload.get("query"),

        limit=payload.get("limit", 20),

        offset=payload.get("offset", 0),

        user_id=payload.get("user_id"),

        universe_id=payload.get("universe_id"),

        content_type=payload.get("content_type"),

        feed_mode=payload.get("feed_mode"),

        blocks_config=payload.get("blocks_config"),
    )

    return {
        "status": "ok",
        "result": result,
    }
