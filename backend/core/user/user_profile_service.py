from typing import Optional, Dict
from datetime import datetime

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
    insert_bq,
    update_bq,
)

TABLE_USER_PROFILE = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_PROFILE"
)

# =========================================================
# GET USER PROFILE
# =========================================================

def get_user_profile(
    user_id: str
) -> Optional[Dict]:

    rows = query_bq(
        f"""
        SELECT
            GEOGRAPHY_1,
            GEOGRAPHY_2,
            GEOGRAPHY_3,
            PROFILE_TEXT
        FROM `{TABLE_USER_PROFILE}`
        WHERE ID_USER = @user_id
        LIMIT 1
        """,
        {
            "user_id": user_id
        }
    )

    if not rows:
        return None

    row = rows[0]

    return {
        "geography_1": row.get("GEOGRAPHY_1"),
        "geography_2": row.get("GEOGRAPHY_2"),
        "geography_3": row.get("GEOGRAPHY_3"),
        "profile_text": row.get("PROFILE_TEXT"),
    }

# =========================================================
# UPDATE USER PROFILE
# =========================================================

def update_user_profile(
    user_id: str,
    geography_1: Optional[str] = None,
    geography_2: Optional[str] = None,
    geography_3: Optional[str] = None,
    profile_text: Optional[str] = None,
):

    existing = get_user_profile(user_id)

    now = datetime.utcnow()

    # =====================================================
    # UPDATE
    # =====================================================

    if existing:

        update_bq(
            TABLE_USER_PROFILE,
            {
                "GEOGRAPHY_1": geography_1,
                "GEOGRAPHY_2": geography_2,
                "GEOGRAPHY_3": geography_3,
                "PROFILE_TEXT": profile_text,
                "UPDATED_AT": now,
            },
            {
                "ID_USER": user_id,
            }
        )

        return

    # =====================================================
    # INSERT
    # =====================================================

    insert_bq(
        TABLE_USER_PROFILE,
        [
            {
                "ID_USER": user_id,

                "GEOGRAPHY_1": geography_1,
                "GEOGRAPHY_2": geography_2,
                "GEOGRAPHY_3": geography_3,

                "PROFILE_TEXT": profile_text,

                "CREATED_AT": now,
                "UPDATED_AT": now,
            }
        ]
    )
