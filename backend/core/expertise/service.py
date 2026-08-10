# backend/core/expertise/service.py

from api.expertise.models import (
    Expertise,
    ExpertiseContent,
    ExpertiseProfile,
)

from .content_service import (
    load_contents_by_ids,
)

from .profile_service import (
    load_profile,
)

from .selection_engine import (
    select_contents,
)

from core.delivery.service import (
    deliver_knowledge,
)

from core.delivery.models import (
    KnowledgeRequest,
    KnowledgeResult,
)

# ============================================================
# BUILD EXPERTISE
# ============================================================

def build_expertise(
    profile: ExpertiseProfile,
    contents: list[ExpertiseContent],
) -> Expertise:

    return Expertise(

        profile=profile,

        contents=contents,

        count=len(contents),

    )

# ============================================================
# GENERATE EXPERTISE
# ============================================================

def generate_expertise_from_profile(
    user_id: str,
    period_start: str | None = None,
    period_end: str | None = None,
    limit: int | None = None,
    universe_id: str | None = None,
    query: str | None = None,
) -> Expertise:

    profile = load_profile(
        user_id=user_id,
    )

    contents = select_contents(

        profile=profile,

        period_start=period_start,

        period_end=period_end,

        limit=limit,

        universe_id=universe_id,

        query=query,

    )

    return build_expertise(

        profile=profile,

        contents=contents,

    )


# ============================================================
# GENERATE EXPERTISE FROM CONTENTS
# ============================================================

def generate_expertise_from_contents(
    user_id: str,
    content_ids: list[str],
) -> Expertise:

    profile = load_profile(
        user_id=user_id,
    )

    contents = load_contents_by_ids(
        content_ids=content_ids,
    )

    return build_expertise(

        profile=profile,

        contents=contents,

    )

# ============================================================
# GENERATE CAPABILITY
# ============================================================

def generate_capability(
    user_id: str,
    capability: str,
    content_ids: list[str] | None = None,
    number_ids: list[str] | None = None,
) -> str:

    request = KnowledgeRequest(

        user_id=user_id,

        content_ids=content_ids or [],

        number_ids=number_ids or [],

        capabilities=[
            capability,
        ],

    )

    result = deliver_knowledge(
        request,
    )

    return result.capability_results.get(
        capability,
        "",
    )


# ============================================================
# GENERATE KNOWLEDGE
# ============================================================

def generate_knowledge(
    request: KnowledgeRequest,
) -> KnowledgeResult:
    """
    Generate one or more capabilities from an Expertise.

    This is the public entry point used by Workspace,
    Digests and future MCP conversations.
    """

    return deliver_knowledge(
        request,
    )
