# backend/core/digest/service.py

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
# GENERATE DIGEST REVIEW
# ============================================================

def generate_digest_review(
    request: DigestRequest,
) -> DigestReview:

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

            expertise=expertise,

            capabilities=request.capabilities,

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
