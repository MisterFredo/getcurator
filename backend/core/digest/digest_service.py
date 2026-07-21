# backend/core/digest/digest_service.py

from core.digest.models import (
    Digest,
    DigestRequest,
)

from core.digest.repository import (
    insert_digest,
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


# ============================================================
# GENERATE
# ============================================================

def generate_digest(
    digest: Digest,
    request: DigestRequest,
) -> Digest:
    """
    Generate a personalized Digest.
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
    # DIGEST
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
    Return a generated Digest.
    """

    digest = fetch_digest(
        digest_id,
    )

    if digest is None:

        raise ValueError(
            f"Unknown digest: {digest_id}"
        )

    return digest
