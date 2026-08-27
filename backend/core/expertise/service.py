# backend/core/expertise/service.py

from time import perf_counter

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
    include_keywords: bool = True,
    apply_profile_selection: bool = True,
    allowed_universe_ids: list[str] | None = None,
) -> Expertise:

    t0 = perf_counter()

    # ========================================================
    # PROFILE
    # ========================================================

    profile = load_profile(
        user_id=user_id,
    )

    # ========================================================
    # OPTIONAL KEYWORD EXCLUSION
    # ========================================================

    if not include_keywords:

        profile = profile.model_copy(

            update={

                "keywords":
                    [],

            },

        )

    t1 = perf_counter()

    print(
        "⏱️ EXPERTISE load_profile:",
        round(
            t1 - t0,
            3,
        ),
        "s",
    )

    # ========================================================
    # CONTENT SELECTION
    # ========================================================

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

        apply_profile_selection=apply_profile_selection,
        allowed_universe_ids=allowed_universe_ids,

    )

    t2 = perf_counter()

    print(
        "⏱️ EXPERTISE select_contents:",
        round(
            t2 - t1,
            3,
        ),
        "s",
    )

    # ========================================================
    # BUILD
    # ========================================================

    expertise = build_expertise(

        profile=profile,

        contents=contents,

        count=total,

    )

    t3 = perf_counter()

    print(
        "⏱️ EXPERTISE build_expertise:",
        round(
            t3 - t2,
            3,
        ),
        "s",
    )

    print(
        "⏱️ EXPERTISE TOTAL:",
        round(
            t3 - t0,
            3,
        ),
        "s",
    )

    return expertise


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
