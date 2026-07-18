from fastapi import APIRouter

from core.digest.models import (
    UserDigestRunRequest,
    ExpertDigestRunRequest,
)

from core.digest.service import (
    run_user_digest,
    run_expert_digest,
    list_digest_reviews,
    get_digest_review,
    send_digest_review,
)

router = APIRouter()


# ============================================================
# USER DIGEST
# ============================================================

@router.post("/run-user")
def run_user_digest_route(
    request: UserDigestRunRequest,
):

    return run_user_digest(
        user_id=request.user_id,
    )


# ============================================================
# EXPERT DIGEST
# ============================================================

@router.post("/run-expert")
def run_expert_digest_route(
    request: ExpertDigestRunRequest,
):

    return run_expert_digest(
        expert_id=request.expert_id,
    )


# ============================================================
# REVIEWS
# ============================================================

@router.get("/reviews")
def list_reviews():

    return list_digest_reviews()


@router.get("/reviews/{review_id}")
def get_review(
    review_id: str,
):

    return get_digest_review(
        review_id,
    )


# ============================================================
# SEND
# ============================================================

@router.post("/reviews/{review_id}/send")
def send_review_route(
    review_id: str,
):

    return send_digest_review(
        review_id,
    )
