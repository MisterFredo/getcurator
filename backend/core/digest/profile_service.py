from typing import Literal

from config import BQ_DATASET, BQ_PROJECT

from utils.bigquery_utils import query_bq

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
    frequency: Literal[
        "weekly",
        "monthly",
    ],
) -> list[DigestRecipient]:
       """
        Return every active recipient matching
        the requested audience and frequency.
        """
    
        if audience == "user":
    
            return _get_user_recipients(
                frequency,
            )
    
        if audience == "expert":
    
            return _get_expert_recipients(
                frequency,
            )
    
        raise ValueError(
            f"Unknown audience: {audience}",
        )


# ============================================================
# USERS
# ============================================================

def _get_user_recipients(
    frequency: str,
) -> list[DigestRecipient]:

    return _load_recipients(
        profile_type="USER",
        frequency=frequency,
    )

# ============================================================
# EXPERTS
# ============================================================

def _get_expert_recipients(
    frequency: str,
) -> list[DigestRecipient]:

    return _load_recipients(
        profile_type="EXPERT",
        frequency=frequency,
    )

# ============================================================
# INTERNAL
# ============================================================

def _load_recipients(
    profile_type: str,
    frequency: str,
) -> list[DigestRecipient]:

    sql = f"""
        SELECT

            ID_USER,
            LANGUAGE

        FROM `{TABLE_USER}`

        WHERE PROFILE_TYPE = @profile_type

          AND IS_ACTIVE = TRUE

          AND UPPER(
              COALESCE(
                  FREQUENCY,
                  ""
              )
          ) = UPPER(
              @frequency
          )

        ORDER BY EMAIL
    """

    rows = query_bq(
        sql,
        {
            "profile_type":
                profile_type,

            "frequency":
                frequency,
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
