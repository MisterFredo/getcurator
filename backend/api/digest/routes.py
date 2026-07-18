# backend/api/digest/routes.py

from fastapi import APIRouter

from core.digest.service import (
    run_user_digest,
    run_expert_digest,
    send_digest_review,
    get_digest_review,
    list_digest_reviews,
)

router = APIRouter()


# ============================================================
# USER DIGEST
# ============================================================

@router.post("/run-user")
def run_user_digest_route(
    payload: dict,
):

    return run_user_digest(

        user_id=payload["user_id"],

    )


# ============================================================
# EXPERT DIGEST
# ============================================================

@router.post("/run-expert")
def run_expert_digest_route(
    payload: dict,
):

    return run_expert_digest(

        expert_id=payload["expert_id"],

    )


# ============================================================
# REVIEWS
# ============================================================

@router.get("/reviews")
def reviews():

    return list_digest_reviews()


@router.get("/reviews/{review_id}")
def review(
    review_id: str,
):

    return get_digest_review(
        review_id,
    )


# ============================================================
# SEND
# ============================================================

@router.post("/reviews/{review_id}/send")
def send_review(
    review_id: str,
):

    return send_digest_review(
        review_id,
    )
