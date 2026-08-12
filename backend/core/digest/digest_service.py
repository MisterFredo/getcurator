# backend/core/digest/digest_service.py

from datetime import (
    datetime,
    timezone,
)

from core.digest.models import (
    Digest,
)

from core.digest.repository import (
    fetch_digest,
    fetch_campaign,
    fetch_digests_for_user,
    update_digest,
)

from core.digest.repository import (
    fetch_digest,
    fetch_campaign,
    fetch_digest_history,
    search_digest_history,
    update_digest,
)

from core.digest.document_service import (
    build_digest_document,
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

from core.expertise.capabilities import (
    CAPABILITY_EXECUTIVE_SUMMARY,
    CAPABILITY_KEY_POINTS,
    CAPABILITY_IMPLICATIONS,
)

from core.digest.send_service import (
    send_digest as deliver_digest,
)

from core.user.user_service import (
    get_user,
)

from core.digest.digest_profile_service import (
    build_digest_profile,
)

# ============================================================
# CONFIGURATION
# ============================================================

DIGEST_CAPABILITIES = [
    CAPABILITY_EXECUTIVE_SUMMARY,
    CAPABILITY_KEY_POINTS,
    CAPABILITY_IMPLICATIONS,
]

DEFAULT_DIGEST_LIMIT = 20


# ============================================================
# GENERATE
# ============================================================

def generate_digest(
    digest_id: str,
) -> Digest:
    """
    Generate a personalized Digest.
    """

    digest = fetch_digest(
        digest_id,
    )

    if digest is None:

        raise ValueError(
            f"Unknown digest: {digest_id}"
        )

    campaign = fetch_campaign(
        digest.campaign_id,
    )

    if campaign is None:

        raise ValueError(
            f"Unknown campaign: {digest.campaign_id}"
        )

    # ========================================================
    # START
    # ========================================================

    digest.status = "generating"

    digest.error = None

    update_digest(
        digest,
    )

    try:

        # ====================================================
        # BUILD PROFILE
        # ====================================================

        profile = build_digest_profile(
            digest.user_id,
        )

        # ====================================================
        # BUILD EXPERTISE
        # ====================================================

        expertise = generate_expertise_from_profile(

            user_id=digest.user_id,

            period_start=campaign.period_start.isoformat(),

            period_end=campaign.period_end.isoformat(),

            limit=DEFAULT_DIGEST_LIMIT,

        )

        # ====================================================
        # DELIVERY
        # ====================================================

        knowledge = deliver_knowledge(

            KnowledgeRequest(

                user_id=digest.user_id,

                capabilities=DIGEST_CAPABILITIES,

                expertise=expertise,

            )

        )

        # ====================================================
        # BUILD DOCUMENT
        # ====================================================

        digest.total_contents = expertise.count

        digest.analyzed_contents = len(
            expertise.contents,
        )

        digest.knowledge = knowledge

        digest.document = build_digest_document(

            profile=profile,

            knowledge=knowledge,

            period_start=campaign.period_start,

            period_end=campaign.period_end,
            frequency=campaign.frequency,
            audience=campaign.audience,

        )

        digest.status = "generated"

        digest.generated_at = datetime.now(
            timezone.utc,
        )

        digest.error = None

    except Exception as exc:

        digest.status = "failed"

        digest.error = str(exc)

        raise

    finally:

        update_digest(
            digest,
        )

    return digest


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

# ============================================================
# SEND
# ============================================================

def send_digest(
    digest_id: str,
) -> Digest:
    """
    Send a generated Digest.
    """

    digest = fetch_digest(
        digest_id,
    )

    if digest is None:

        raise ValueError(
            f"Unknown digest: {digest_id}"
        )

    if digest.document is None:

        raise ValueError(
            "Digest has not been generated."
        )

    user = get_user(
        digest.user_id,
    )

    if user is None:

        raise ValueError(
            f"Unknown user: {digest.user_id}"
        )

    # ========================================================
    # START
    # ========================================================

    digest.status = "sending"

    digest.error = None

    update_digest(
        digest,
    )

    try:

        deliver_digest(

            document=digest.document,

            recipient=user["EMAIL"],

        )

        digest.status = "sent"

        digest.sent_at = datetime.now(
            timezone.utc,
        )

        digest.error = None

    except Exception as exc:

        digest.status = "generated"

        digest.error = str(exc)

        raise

    finally:

        update_digest(
            digest,
        )

    return digest


# ============================================================
# LIST FOR PROFILE
# ============================================================

def list_digests_for_profile(
    user_id: str,
) -> list[Digest]:
    """
    Return generated Digests for a profile.
    """

    return fetch_digests_for_user(
        user_id,
    )

# ============================================================
# HISTORY
# ============================================================

def list_digest_history(
    profile_id: str,
) -> list[dict]:
    """
    Return available Digest history
    for a user/profile.
    """

    return fetch_digest_history(
        profile_id,
    )

def search_digests(
    query: str | None = None,
    user_id: str | None = None,
    company_id: str | None = None,
    solution_id: str | None = None,
    topic_id: str | None = None,
) -> list[dict]:

    return search_digest_history(
        query=query,
        user_id=user_id,
        company_id=company_id,
        solution_id=solution_id,
        topic_id=topic_id,
    )
