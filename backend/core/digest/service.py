from datetime import (
    datetime,
    timedelta,
    timezone,
)

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


# ============================================================
# RUN USER DIGEST
# ============================================================

def run_user_digest(
    user_id: str,
) -> DigestReview:

    request = DigestRequest(

        user_id=user_id,

        target_type="user",

        period_start=(
            datetime.now(timezone.utc)
            - timedelta(days=7)
        ),

        period_end=datetime.now(
            timezone.utc
        ),

        capabilities=[
            "summary",
            "implications",
        ],

    )

    return generate_digest_review(
        request,
    )


# ============================================================
# RUN EXPERT DIGEST
# ============================================================

def run_expert_digest(
    expert_id: str,
) -> DigestReview:

    # TODO
    # Charger l'expert afin de récupérer
    # le user_id associé.

    request = DigestRequest(

        user_id="",

        target_type="expert",

        expert_id=expert_id,

        period_start=(
            datetime.now(timezone.utc)
            - timedelta(days=30)
        ),

        period_end=datetime.now(
            timezone.utc
        ),

        capabilities=[
            "summary",
            "implications",
        ],

    )

    return generate_digest_review(
        request,
    )


# ============================================================
# LIST REVIEWS
# ============================================================

def list_digest_reviews():

    raise NotImplementedError


# ============================================================
# GET REVIEW
# ============================================================

def get_digest_review(
    review_id: str,
):

    raise NotImplementedError


# ============================================================
# SEND REVIEW
# ============================================================

def send_digest_review(
    review_id: str,
):

    raise NotImplementedError
