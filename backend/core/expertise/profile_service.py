# backend/core/expertise/profile_service.py

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
    get_user,
)


# ============================================================
# LOAD PROFILE
# ============================================================

def load_profile(
    user_id: str,
) -> ExpertiseProfile:

    # ========================================================
    # USER
    # ========================================================

    user = (
        get_user(
            user_id,
        )
        or {}
    )

    # ========================================================
    # PROFILE
    # ========================================================

    profile = (
        get_user_profile(
            user_id,
        )
        or {}
    )

    # ========================================================
    # PREFERENCES
    # ========================================================

    preferences = (
        get_user_preferences_grouped(
            user_id,
        )
        or {}
    )

    # ========================================================
    # KEYWORDS
    # ========================================================

    keywords = (
        get_user_keywords(
            user_id,
        )
        or []
    )

    # ========================================================
    # GEOGRAPHIES
    # ========================================================

    geographies = [

        geography

        for geography in (

            profile.get(
                "geography_1",
            ),

            profile.get(
                "geography_2",
            ),

            profile.get(
                "geography_3",
            ),

        )

        if geography

    ]

    # ========================================================
    # PROFILE
    # ========================================================

    return ExpertiseProfile(

        id=user_id,

        language=(
            user.get(
                "LANGUAGE",
            )
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
                "profile_text",
            )
            or ""
        ),

    )
