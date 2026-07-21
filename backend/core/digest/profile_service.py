from typing import Literal

from core.digest.models import (
    DigestRecipient,
)

Audience = Literal[
    "user",
    "expert",
]


# ============================================================
# PUBLIC
# ============================================================

def get_digest_recipients(
    audience: Audience,
) -> list[DigestRecipient]:
    """
    Return every active recipient for
    the requested audience.
    """

    if audience == "user":
        return _get_user_recipients()

    if audience == "expert":
        return _get_expert_recipients()

    raise ValueError(
        f"Unknown audience: {audience}",
    )


# ============================================================
# USERS
# ============================================================

def _get_user_recipients(
) -> list[DigestRecipient]:
    """
    Return every active USER recipient.
    """

    # TODO
    #
    # SELECT
    #     ID_USER,
    #     LANGUAGE
    # FROM RATECARD_USER
    # WHERE PROFILE_TYPE = 'USER'
    #   AND IS_ACTIVE = TRUE
    #

    raise NotImplementedError


# ============================================================
# EXPERTS
# ============================================================

def _get_expert_recipients(
) -> list[DigestRecipient]:
    """
    Return every active EXPERT recipient.
    """

    # TODO
    #
    # SELECT
    #     ID_USER,
    #     LANGUAGE
    # FROM RATECARD_USER
    # WHERE PROFILE_TYPE = 'EXPERT'
    #   AND IS_ACTIVE = TRUE
    #

    raise NotImplementedError
