from core.digest.models import (
    DigestBadge,
    DigestProfile,
)

from core.user.user_service import (
    get_user,
)

from core.user.user_profile_service import (
    get_user_profile,
)

from core.user.user_preferences_service import (
    get_user_preferences_detailed,
)

from core.user.user_keyword_service import (
    get_user_keywords,
)


# ============================================================
# BUILD DIGEST PROFILE
# ============================================================

def build_digest_profile(
    user_id: str,
) -> DigestProfile:
    """
    Build the profile snapshot used to personalize
    one DigestDocument.
    """

    # ========================================================
    # LOAD USER
    # ========================================================

    user = get_user(
        user_id,
    )

    if not user:

        raise ValueError(
            f"Unknown user: {user_id}"
        )

    # ========================================================
    # LOAD PROFILE
    # ========================================================

    profile = (
        get_user_profile(
            user_id,
        )
        or {}
    )

    # ========================================================
    # LOAD PREFERENCES
    # ========================================================

    preferences = (
        get_user_preferences_detailed(
            user_id,
        )
        or {}
    )

    # ========================================================
    # LOAD KEYWORDS
    # ========================================================

    keywords = (
        get_user_keywords(
            user_id,
        )
        or []
    )

    # ========================================================
    # BUILD
    # ========================================================

    return DigestProfile(

        name=(

            user.get("DISPLAY_NAME")

            or user.get("NAME")

            or ""

        ),

        company=user.get(
            "COMPANY"
        ),

        role=user.get(
            "ROLE"
        ),

        description=profile.get(
            "profile_text"
        ),

        geography_1=profile.get(
            "geography_1"
        ),

        geography_2=profile.get(
            "geography_2"
        ),

        geography_3=profile.get(
            "geography_3"
        ),

        companies=_build_badges(

            preferences.get(
                "companies",
                [],
            ),

            "company",

        ),

        topics=_build_badges(

            preferences.get(
                "topics",
                [],
            ),

            "topic",

        ),

        solutions=_build_badges(

            preferences.get(
                "solutions",
                [],
            ),

            "solution",

        ),

        keywords=keywords,

    )


# ============================================================
# HELPERS
# ============================================================

def _build_badges(
    values: list[dict],
    badge_type: str,
) -> list[DigestBadge]:

    badges = []

    for value in values:

        label = value.get(
            "label"
        )

        if not label:

            continue

        badges.append(

            DigestBadge(

                label=label,

                type=badge_type,

            )

        )

    return badges
