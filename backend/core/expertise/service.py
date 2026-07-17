# backend/core/expertise/service.py

from api.expertise.models import (
    Expertise,
    ExpertiseContext,
)

from .insight_engine import (
    generate_insights,
)

from .profile_service import (
    load_profile,
)

from .selection_engine import (
    select_contents,
)


# ============================================================
# BUILD EXPERTISE
# ============================================================

def _build_expertise(
    profile: ExpertiseProfile,
    contents: list[ExpertiseContent],
) -> Expertise:

    context = ExpertiseContext(
        profile=profile,
        contents=contents,
        count=len(contents),
    )

    insights = generate_insights(
        profile=context.profile,
        contents=context.contents,
    )

    return Expertise(
        profile=context.profile,
        contents=context.contents,
        count=context.count,
        summary=insights.summary,
        implications=insights.implications,
    )


# ============================================================
# GENERATE EXPERTISE CONTEXT
# ============================================================

def generate_expertise_context(
    user_id: str,
    period_start: str | None = None,
    period_end: str | None = None,
    limit: int | None = None,
) -> ExpertiseContext:

    profile = load_profile(
        user_id=user_id,
    )

    contents = select_contents(
        profile=profile,
        period_start=period_start,
        period_end=period_end,
        limit=limit,
    )

    return ExpertiseContext(

        profile=profile,

        contents=contents,

        count=len(contents),

    )

# ============================================================
# GENERATE EXPERTISE
# ============================================================

def generate_expertise(
    user_id: str,
    period_start: str | None = None,
    period_end: str | None = None,
    limit: int | None = None,
) -> Expertise:

    context = generate_expertise_context(
        user_id=user_id,
        period_start=period_start,
        period_end=period_end,
        limit=limit,
    )

    return _build_expertise(
        profile=context.profile,
        contents=context.contents,
    )

# ============================================================
# GENERATE EXPERTISE FROM CONTENTS
# ============================================================

def generate_expertise_from_contents(
    user_id: str,
    content_ids: list[str],
) -> Expertise:

    # ========================================================
    # PROFILE
    # ========================================================

    profile = load_profile(
        user_id=user_id,
    )

    # ========================================================
    # CONTENTS
    # ========================================================

    contents = load_contents_by_ids(
        content_ids=content_ids,
    )

    # ========================================================
    # BUILD
    # ========================================================

    return _build_expertise(
        profile=profile,
        contents=contents,
    )
