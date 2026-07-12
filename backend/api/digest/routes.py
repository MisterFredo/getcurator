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
# CREATE DIGEST
# ============================================================

@router.post("/create")
def create_digest_route(
    payload: dict,
):

    from core.digest.digest_service import (
        create_digest,
    )

    result = create_digest(

        user_id=payload.get(
            "user_id"
        ),

        digest_name=payload.get(
            "digest_name"
        ),

        frequency=payload.get(
            "frequency",
            "WEEKLY",
        ),

        content_ids=payload.get(
            "content_ids",
            [],
        ),

        summary=payload.get(
            "summary",
            "",
        ),

        implications=payload.get(
            "implications",
            "",
        ),
    )

    return {
        "status": "ok",
        "result": result,
    }

# ============================================================
# LIST DIGESTS
# ============================================================

@router.get("/list")
def list_digests_route(
    user_id: str,
):

    from core.digest.digest_service import (
        list_digests,
    )

    result = list_digests(
        user_id=user_id,
    )

    return {
        "status": "ok",
        "result": result,
    }

# ============================================================
# LIST ALL DIGESTS
# ============================================================

@router.get("/list-all")
def list_all_digests_route():

    from core.digest.digest_service import (
        list_all_digests,
    )

    result = list_all_digests()

    return {
        "status": "ok",
        "result": result,
    }


# ============================================================
# MY FEED
# ============================================================

@router.get("/my-feed")
def digest_my_feed(

    user_id: str = Query(...),

    period_start: str | None = Query(
        None
    ),

    period_end: str | None = Query(
        None
    ),

    limit: int | None = Query(
        None
    ),
):

    result = get_digest_contents(

        user_id=user_id,

        period_start=period_start,

        period_end=period_end,

        limit=limit,
    )

    return {
        "status": "ok",

        "result": result,
    }

# ============================================================
# LOG SEND (LEGACY)
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


# ============================================================
# GENERATE EDITORIAL
# ============================================================

@router.post("/generate-editorial")
def generate_editorial(
    payload: dict,
):

    ids = payload.get(
        "ids",
        [],
    )

    result = run_insight_pipeline(
        ids
    )

    return {
        "status": "ok",
        **result,
    }

# ============================================================
# SAVE DIGEST
# ============================================================

# ============================================================
# SAVE DIGEST
# ============================================================

@router.post("/{digest_id}/save")
def save_digest_route(
    digest_id: str,
    payload: dict,
):

    from core.digest.digest_service import (
        save_digest,
    )

    result = save_digest(

        digest_id=digest_id,

        digest_name=payload.get(
            "digest_name"
        ),

        summary=payload.get(
            "summary"
        ),

        implications=payload.get(
            "implications"
        ),

        content_ids=payload.get(
            "content_ids",
            [],
        ),
    )

    return {
        "status": "ok",
        "result": result,
    }


# ============================================================
# GENERATE ANALYSIS (PREVIEW)
# ============================================================

@router.post("/generate-analysis")
def generate_digest_analysis_route(
    payload: dict,
):

    from core.digest.analysis_service import (
        generate_digest_analysis_from_ids,
    )

    result = generate_digest_analysis_from_ids(

        user_id=payload.get(
            "user_id"
        ),

        content_ids=payload.get(
            "content_ids",
            [],
        ),
    )

    return {
        "status": "ok",
        "result": result,
    }


# ============================================================
# REGENERATE ANALYSIS
# ============================================================

@router.post("/{digest_id}/regenerate-analysis")
def regenerate_analysis_route(
    digest_id: str,
):

    from core.digest.digest_service import (
        regenerate_analysis,
    )

    result = regenerate_analysis(
        digest_id=digest_id,
    )

    return {
        "status": "ok",
        "result": result,
    }


# ============================================================
# SEND DIGEST
# ============================================================

@router.post("/{digest_id}/send")
def send_digest_route(
    digest_id: str,
):

    from core.digest.digest_service import (
        send_digest,
    )

    result = send_digest(
        digest_id=digest_id,
    )

    return {
        "status": "ok",
        "result": result,
    }


# ============================================================
# GET DIGEST
# ============================================================

@router.get("/{digest_id}")
def get_digest_route(
    digest_id: str,
):

    from core.digest.digest_service import (
        get_digest,
    )

    result = get_digest(
        digest_id=digest_id,
    )

    return {
        "status": "ok",
        "result": result,
    }


# ============================================================
# DELETE DIGEST
# ============================================================

@router.delete("/{digest_id}")
def delete_digest_route(
    digest_id: str,
):

    from core.digest.digest_service import (
        delete_digest,
    )

    result = delete_digest(
        digest_id=digest_id,
    )

    return {
        "status": "ok",
        "result": result,
    }
