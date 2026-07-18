# backend/api/digest/routes.py

from fastapi import APIRouter

from core.digest.models import (
    DigestRequest,
    DigestReview,
)

from core.digest.service import (
    generate_digest_review,
)

from core.digest.render_service import (
    render_digest,
)

from core.digest.pipeline import (
    run_digest,
)

router = APIRouter()


# ============================================================
# REVIEW
# ============================================================

@router.post("/review")
def review_digest(
    request: DigestRequest,
) -> DigestReview:

    return generate_digest_review(
        request,
    )


# ============================================================
# DOCUMENT
# ============================================================

@router.post("/document")
def render_digest_document(
    review: DigestReview,
):

    return render_digest(
        review,
    )


# ============================================================
# SEND
# ============================================================

@router.post("/send")
def send_digest(
    request: DigestRequest,
    recipient: str,
):

    run_digest(
        request=request,
        recipient=recipient,
    )

    return {
        "status": "ok",
    }
