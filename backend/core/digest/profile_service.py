from typing import Literal

from core.digest.models import (
    DigestProfile,
)


# ============================================================
# PUBLIC
# ============================================================

def get_digest_profiles(
    frequency: Literal[
        "weekly",
        "monthly",
    ],
    audience: Literal[
        "user",
        "expert",
    ],
) -> list[DigestProfile]:
    """
    Return every profile eligible for a DigestBatch.
    """

    if audience == "user":

        return _get_user_profiles(
            frequency=frequency,
        )

    elif audience == "expert":

        return _get_expert_profiles(
            frequency=frequency,
        )

    raise ValueError(
        f"Unknown audience: {audience}"
    )


# ============================================================
# USERS
# ============================================================

def _get_user_profiles(
    frequency: Literal[
        "weekly",
        "monthly",
    ],
) -> list[DigestProfile]:
    """
    Return every active USER profile.
    """

    # TODO
    # Query RATECARD_USER
    # WHERE PROFILE_TYPE='USER'
    # AND STATUS='ACTIVE'

    raise NotImplementedError


# ============================================================
# EXPERTS
# ============================================================

def _get_expert_profiles(
    frequency: Literal[
        "weekly",
        "monthly",
    ],
) -> list[DigestProfile]:
    """
    Return every active EXPERT profile.
    """

    # TODO
    # Query RATECARD_USER
    # WHERE PROFILE_TYPE='EXPERT'
    # AND STATUS='ACTIVE'

    raise NotImplementedError
