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
    get_user_context,
)


# ============================================================
# LOAD PROFILE
# ============================================================

def load_profile(
    user_id: str,
) -> ExpertiseProfile:

    context = (
        get_user_context(user_id)
        or {}
    )

    profile = (
        get_user_profile(user_id)
        or {}
    )

    preferences = (
        get_user_preferences_grouped(user_id)
        or {}
    )

    keywords = (
        get_user_keywords(user_id)
        or []
    )

    geographies = [

        geography

        for geography in (

            profile.get("geography_1"),

            profile.get("geography_2"),

            profile.get("geography_3"),

        )

        if geography

    ]

    return ExpertiseProfile(

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
            profile.get("profile_text")
            or ""
        ),

    )
