from core.digest.models import (
    DigestRequest,
    DigestReview,
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
    request: DigestRequest,
) -> DigestReview:
    """
    Generate a digest review for a single profile.
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

    return DigestReview(

        request=request,

        total_contents=expertise.count,

        analyzed_contents=expertise.count,

        knowledge=knowledge,

    )


# ============================================================
# REVIEWS
# ============================================================

def list_digest_reviews():

    raise NotImplementedError


def get_digest_review(
    review_id: str,
):

    raise NotImplementedError
