# backend/core/digest/profile_service.py

from core.digest.models import (
    DigestProfile,
)


# ============================================================
# PUBLIC
# ============================================================

def get_digest_profiles(
    frequency: str,
    audience: str,
) -> list[DigestProfile]:
    """
    Return every profile eligible for a DigestBatch.
    """

    if audience == "user":

        return _get_user_profiles(
            frequency=frequency,
        )

    if audience == "expert":

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
    frequency: str,
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
    frequency: str,
) -> list[DigestProfile]:
    """
    Return every active EXPERT profile.
    """

    # TODO
    # Query RATECARD_USER
    # WHERE PROFILE_TYPE='EXPERT'
    # AND STATUS='ACTIVE'

    raise NotImplementedError
