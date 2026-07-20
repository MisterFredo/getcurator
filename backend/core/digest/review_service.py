from core.digest.models import (
    DigestRequest,
    DigestReview,
)

from core.digest.review_repository import (
    insert_review,
    fetch_review,
    fetch_reviews,
)

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from core.expertise.service import (
    generate_expertise_from_profile,
)

from core.delivery.models import (
    KnowledgeRequest,
)

from core.delivery.service import (
    deliver_knowledge,
)


# ============================================================
# GENERATE REVIEW
# ============================================================

def generate_review(
    request:Request,
) -> Review:
    """
    Generate and persist a Review.
    """

    # ========================================================
    # BUILD EXPERTISE
    # ========================================================

    expertise = generate_expertise_from_profile(

        user_id=request.user_id,

        period_start=request.period_start.isoformat(),

        period_end=request.period_end.isoformat(),

        limit=request.limit,

    )

    # ========================================================
    # DELIVERY
    # ========================================================

    knowledge = deliver_knowledge(

        KnowledgeRequest(

            user_id=request.user_id,

            capabilities=request.capabilities,

            expertise=expertise,

        )

    )

    # ========================================================
    # REVIEW
    # ========================================================

    review = Review(

        request=request,

        total_contents=expertise.count,

        analyzed_contents=len(
            expertise.contents,
        ),

        knowledge=knowledge,

    )

    # ========================================================
    # PERSIST
    # ========================================================

    return insert_review(
        review,
    )

# ============================================================
# GET
# ============================================================

def get_review(
    review_id: str,
) -> Review:
    """
    Return a Review.
    """

    review = fetch_review(
        review_id=review_id,
    )

    if review is None:

        raise ValueError(
            f"Unknown review: {review_id}"
        )

    return review

# ============================================================
# LIST
# ============================================================

def list_reviews() -> list[Review]:
    """
    Return the latest Review history.
    """

    return fetch_reviews()


