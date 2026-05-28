# backend/api/digest/routes.py

from fastapi import (
    APIRouter,
    Query,
)

from core.digest.content_service import (
    get_digest_contents,
)

from core.digest.send_service import (
    log_digest_send,
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

# ============================================================
# LOG SEND
# ============================================================

@router.post("/log-send")
def digest_log_send(
    payload: dict,
):

    result = log_digest_send(
        user_id=payload.get(
            "user_id"
        ),

        nb_contents=payload.get(
            "nb_contents",
            0,
        ),

        sent_by=payload.get(
            "sent_by",
            "",
        ),

        subject=payload.get(
            "subject",
            "",
        ),
    )

    return {
        "status": "ok",

        "result": result,
    }

@router.post("/generate-editorial")
def generate_editorial(
    payload: dict,
):

    ids = payload.get("ids", [])

    result = run_insight_pipeline(ids)

    return {
        "status": "ok",
        **result,
    }
