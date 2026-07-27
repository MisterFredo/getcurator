# backend/core/digest/digest_service.py

from datetime import (
    datetime,
    timezone,
)

from core.digest.models import (
    Campaign,
    Digest,
)

from core.digest.repository import (
    update_digest,
    fetch_digest,
)

from core.digest.render_service import (
    render_digest,
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

from core.expertise.constants import (
    OUTPUT_SUMMARY,
    OUTPUT_IMPLICATIONS,
)

# ============================================================
# CONFIGURATION
# ============================================================

DIGEST_CAPABILITIES = [
    OUTPUT_SUMMARY,
    OUTPUT_IMPLICATIONS,
]

DEFAULT_DIGEST_LIMIT = 20


# ============================================================
# GENERATE
# ============================================================

def generate_digest(
    digest: Digest,
    campaign: Campaign,
) -> Digest:
    """
    Generate a personalized Digest.
    """

    # ========================================================
    # BUILD EXPERTISE
    # ========================================================

    expertise = generate_expertise_from_profile(

        user_id=digest.user_id,

        period_start=campaign.period_start.isoformat(),

        period_end=campaign.period_end.isoformat(),

        limit=DEFAULT_DIGEST_LIMIT,

    )

    # ========================================================
    # DELIVERY
    # ========================================================

    knowledge = deliver_knowledge(

        KnowledgeRequest(

            user_id=digest.user_id,

            capabilities=DIGEST_CAPABILITIES,

            expertise=expertise,

        )

    )

    # ========================================================
    # BUILD DOCUMENT
    # ========================================================

    digest.total_contents = expertise.count

    digest.analyzed_contents = len(
        expertise.contents,
    )

    digest.knowledge = knowledge

    digest.document = render_digest(

        knowledge=knowledge,

        expertise=expertise,

    )

    digest.status = "generated"

    digest.generated_at = datetime.now(
        timezone.utc,
    )

    # ========================================================
    # PERSIST
    # ========================================================

    return update_digest(
        digest,
    )


# ============================================================
# GET
# ============================================================

def get_digest(
    digest_id: str,
) -> Digest:
    """
    Return a Digest.
    """

    digest = fetch_digest(
        digest_id,
    )

    if digest is None:

        raise ValueError(
            f"Unknown digest: {digest_id}"
        )

    return digest
