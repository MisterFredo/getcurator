# backend/core/expertise/profile_service.py

from time import perf_counter

from api.expertise.models import (
    ExpertisePreferences,
    ExpertiseProfile,
)

from core.user.user_keyword_service import (
    get_user_keywords,
)

from core.user.user_profile_service import (
    get_user_profile,
)

from core.user.user_preferences_service import (
    get_user_preferences_grouped,
)

from core.user.user_service import (
    get_user_context,
)


# ============================================================
# LOAD PROFILE
# ============================================================

def load_profile(
    user_id: str,
) -> ExpertiseProfile:

    t0 = perf_counter()

    # ========================================================
    # USER CONTEXT
    # ========================================================

    context = (
        get_user_context(
            user_id
        )
        or {}
    )

    t1 = perf_counter()

    print(
        "⏱️ PROFILE get_user_context:",
        round(
            t1 - t0,
            3,
        ),
        "s",
    )

    # ========================================================
    # USER PROFILE
    # ========================================================

    profile = (
        get_user_profile(
            user_id
        )
        or {}
    )

    t2 = perf_counter()

    print(
        "⏱️ PROFILE get_user_profile:",
        round(
            t2 - t1,
            3,
        ),
        "s",
    )

    # ========================================================
    # PREFERENCES
    # ========================================================

    preferences = (
        get_user_preferences_grouped(
            user_id
        )
        or {}
    )

    t3 = perf_counter()

    print(
        "⏱️ PROFILE get_user_preferences:",
        round(
            t3 - t2,
            3,
        ),
        "s",
    )

    # ========================================================
    # KEYWORDS
    # ========================================================

    keywords = (
        get_user_keywords(
            user_id
        )
        or []
    )

    t4 = perf_counter()

    print(
        "⏱️ PROFILE get_user_keywords:",
        round(
            t4 - t3,
            3,
        ),
        "s",
    )

    # ========================================================
    # GEOGRAPHIES
    # ========================================================

    geographies = [

        geography

        for geography in (

            profile.get(
                "geography_1"
            ),

            profile.get(
                "geography_2"
            ),

            profile.get(
                "geography_3"
            ),

        )

        if geography

    ]

    # ========================================================
    # BUILD PROFILE
    # ========================================================

    result = ExpertiseProfile(

        id=user_id,

        language=(
            context.get("lang")
            or "fr"
        ).lower(),

        preferences=ExpertisePreferences(

            companies=preferences.get(
                "COMPANY",
                [],
            ),

            solutions=preferences.get(
                "SOLUTION",
                [],
            ),

            topics=preferences.get(
                "TOPIC",
                [],
            ),

        ),

        keywords=keywords,

        geographies=geographies,

        profile_text=(
            profile.get(
                "profile_text"
            )
            or ""
        ),

    )

    t5 = perf_counter()

    print(
        "⏱️ PROFILE build:",
        round(
            t5 - t4,
            3,
        ),
        "s",
    )

    print(
        "⏱️ PROFILE TOTAL:",
        round(
            t5 - t0,
            3,
        ),
        "s",
    )

    return result
