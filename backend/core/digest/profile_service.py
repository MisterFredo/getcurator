from typing import Literal

from config import (
    BQ_DATASET,
    BQ_PROJECT,
)

from utils.bigquery_utils import (
    query_bq,
)

from core.digest.models import (
    DigestRecipient,
)


# ============================================================
# TYPES
# ============================================================

Audience = Literal[
    "user",
    "expert",
]


# ============================================================
# TABLES
# ============================================================

TABLE_USER = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER"
)

TABLE_USER_PREFERENCES = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_PREFERENCES"
)

TABLE_USER_KEYWORD = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_KEYWORD"
)


# ============================================================
# PUBLIC
# ============================================================

def get_digest_recipients(
    audience: Audience,
) -> list[DigestRecipient]:
    """
    Return every active and eligible recipient
    matching the requested audience.

    A profile is eligible when it has at least
    one preference or one keyword.
    """

    if audience == "user":

        return _get_user_recipients()

    if audience == "expert":

        return _get_expert_recipients()

    raise ValueError(
        f"Unknown audience: {audience}",
    )


# ============================================================
# ELIGIBILITY
# ============================================================

def is_digest_profile_eligible(
    user_id: str,
) -> bool:
    """
    Return whether one profile is active and
    has at least one usable Digest criterion.
    """

    rows = query_bq(
        f"""
        SELECT 1

        FROM `{TABLE_USER}` u

        WHERE u.ID_USER = @user_id

          AND u.IS_ACTIVE = TRUE

          AND (

              EXISTS (

                  SELECT 1

                  FROM `{TABLE_USER_PREFERENCES}` p

                  WHERE p.ID_USER = u.ID_USER

              )

              OR EXISTS (

                  SELECT 1

                  FROM `{TABLE_USER_KEYWORD}` k

                  WHERE k.ID_USER = u.ID_USER

              )

          )

        LIMIT 1
        """,
        {
            "user_id":
                user_id,
        },
    )

    return bool(
        rows
    )


# ============================================================
# USERS
# ============================================================

def _get_user_recipients(
) -> list[DigestRecipient]:

    return _load_recipients(
        profile_type="USER",
    )


# ============================================================
# EXPERTS
# ============================================================

def _get_expert_recipients(
) -> list[DigestRecipient]:

    return _load_recipients(
        profile_type="EXPERT",
    )


# ============================================================
# INTERNAL
# ============================================================

def _load_recipients(
    profile_type: str,
) -> list[DigestRecipient]:

    sql = f"""
        SELECT

            u.ID_USER,
            u.LANGUAGE

        FROM `{TABLE_USER}` u

        WHERE u.PROFILE_TYPE = @profile_type

          AND u.IS_ACTIVE = TRUE

          AND (

              EXISTS (

                  SELECT 1

                  FROM `{TABLE_USER_PREFERENCES}` p

                  WHERE p.ID_USER = u.ID_USER

              )

              OR EXISTS (

                  SELECT 1

                  FROM `{TABLE_USER_KEYWORD}` k

                  WHERE k.ID_USER = u.ID_USER

              )

          )

        ORDER BY
            u.EMAIL
    """

    rows = query_bq(
        sql,
        {
            "profile_type":
                profile_type,
        },
    )

    return [

        DigestRecipient(

            user_id=row["ID_USER"],

            language=(
                row.get("LANGUAGE")
                or "en"
            ),

        )

        for row in rows

    ]
