from typing import Literal

from core.digest.models import (
    DigestProfile,
)

# ============================================================
# TYPES
# ============================================================

Audience = Literal[
    "user",
    "expert",
]

# ============================================================
# PUBLIC
# ============================================================

def get_digest_profiles(
    audience: Audience,
) -> list[DigestProfile]:
    """
    Return every active recipient profile
    for the requested audience.
    """

    if audience == "user":
        return _get_user_profiles()

    if audience == "expert":
        return _get_expert_profiles()

    raise ValueError(
        f"Unknown audience: {audience}",
    )

# ============================================================
# USERS
# ============================================================

def _get_user_profiles(
) -> list[DigestProfile]:
    """
    Return every active USER profile.
    """

    # TODO
    #
    # SELECT *
    # FROM RATECARD_USER
    # WHERE PROFILE_TYPE = 'USER'
    #   AND STATUS = 'ACTIVE'
    #

    raise NotImplementedError

# ============================================================
# EXPERTS
# ============================================================

def _get_expert_profiles(
) -> list[DigestProfile]:
    """
    Return every active EXPERT profile.
    """

    # TODO
    #
    # SELECT *
    # FROM RATECARD_USER
    # WHERE PROFILE_TYPE = 'EXPERT'
    #   AND STATUS = 'ACTIVE'
    #

    raise NotImplementedError
