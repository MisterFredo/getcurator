# backend/core/expertise/profile_service.py

from api.expertise.models import (
    ExpertiseProfile,
)

from core.user.user_keyword_service import (
    get_user_keywords,
)

from core.user.user_profile_service import (
    get_user_profile,
)

from .user_repository import (
    load_user,
    load_user_preferences,
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
        load_user(user_id)
        or {}
    )

    # ========================================================
    # PREFERENCES
    # ========================================================

    preferences = (
        load_user_preferences(user_id)
        or {}
    )

    # ========================================================
    # KEYWORDS
    # ========================================================

    keywords = (
        get_user_keywords(user_id)
        or []
    )

    # ========================================================
    # PROFILE
    # ========================================================

    profile = (
        get_user_profile(user_id)
        or {}
    )

    # ========================================================
    # GEOGRAPHIES
    # ========================================================

    geographies = [

        geography

        for geography in (

            profile.get("geography_1"),

            profile.get("geography_2"),

            profile.get("geography_3"),

        )

        if geography

    ]

    # ========================================================
    # RESULT
    # ========================================================

    return ExpertiseProfile(

        id=user_id,

        language=(
            user.get("LANGUAGE")
            or "fr"
        ).lower(),

        preferences=preferences,

        keywords=keywords,

        geographies=geographies,

        profile_text=(
            profile.get("profile_text")
            or ""
        ),
    )
