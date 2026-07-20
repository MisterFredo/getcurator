# backend/core/digest/review_repository.py

from core.digest.models import (
    DigestReview,
)


# ============================================================
# CREATE
# ============================================================

def insert_review(
    review: DigestReview,
) -> DigestReview:
    """
    Persist a new DigestReview.
    """

    raise NotImplementedError


# ============================================================
# UPDATE
# ============================================================

def update_review(
    review: DigestReview,
) -> DigestReview:
    """
    Update an existing DigestReview.
    """

    raise NotImplementedError


# ============================================================
# GET
# ============================================================

def fetch_review(
    review_id: str,
) -> DigestReview | None:
    """
    Return a DigestReview by id.
    """

    raise NotImplementedError


# ============================================================
# LIST
# ============================================================

def fetch_reviews() -> list[DigestReview]:
    """
    Return the latest DigestReviews.
    """

    raise NotImplementedError
