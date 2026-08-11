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


# ============================================================
# BUILD EXPERTISE
# ============================================================

def build_expertise(
    profile: ExpertiseProfile,
    contents: list[ExpertiseContent],
    count: int | None = None,
) -> Expertise:

    return Expertise(

        profile=profile,

        contents=contents,

        count=(
            count
            if count is not None
            else len(contents)
        ),

    )


# ============================================================
# GENERATE EXPERTISE
# ============================================================

def generate_expertise_from_profile(
    user_id: str,
    period_start: str | None = None,
    period_end: str | None = None,
    limit: int | None = None,
    offset: int = 0,
    universe_id: str | None = None,
    query: str | None = None,
    company_id: str | None = None,
    solution_id: str | None = None,
    topic_id: str | None = None,
) -> Expertise:

    profile = load_profile(
        user_id=user_id,
    )

    contents, total = select_contents(

        profile=profile,

        period_start=period_start,

        period_end=period_end,

        limit=limit,

        offset=offset,

        universe_id=universe_id,

        query=query,

        company_id=company_id,

        solution_id=solution_id,

        topic_id=topic_id,

    )

    return build_expertise(

        profile=profile,

        contents=contents,

        count=total,

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
