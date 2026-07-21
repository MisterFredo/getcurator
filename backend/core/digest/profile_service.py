from typing import Literal

from backend.config import (
    BQ_DATASET,
    BQ_PROJECT,
)

from backend.utils.bigquery_utils import (
    query_bq,
)

from core.digest.models import (
    DigestRecipient,
)

Audience = Literal[
    "user",
    "expert",
]

TABLE_USER = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER"
)


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

    return _load_recipients(
        "USER",
    )


# ============================================================
# EXPERTS
# ============================================================

def _get_expert_recipients(
) -> list[DigestRecipient]:

    return _load_recipients(
        "EXPERT",
    )


# ============================================================
# INTERNAL
# ============================================================

def _load_recipients(
    profile_type: str,
) -> list[DigestRecipient]:

    sql = f"""
        SELECT

            ID_USER,
            LANGUAGE

        FROM `{TABLE_USER}`

        WHERE PROFILE_TYPE = @profile_type
          AND IS_ACTIVE = TRUE

        ORDER BY EMAIL
    """

    rows = query_bq(
        sql,
        {
            "profile_type": profile_type,
        },
    )

    return [

        DigestRecipient(

            user_id=row["ID_USER"],

            language=row.get(
                "LANGUAGE",
                "en",
            ),

        )

        for row in rows

    ]
