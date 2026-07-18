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
) -> Expertise:

    profile = load_profile(
        user_id=user_id,
    )

    contents = select_contents(
        profile=profile,
        period_start=period_start,
        period_end=period_end,
        limit=limit,
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
