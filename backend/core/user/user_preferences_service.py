# ============================================================
# IMPORTS
# ============================================================

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq


# ============================================================
# TABLE
# ============================================================

TABLE_USER_PREFERENCES = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_PREFERENCES"
)


# ============================================================
# GET USER PREFERENCES
# ============================================================

def get_user_preferences(user_id: str):
    query = f"""
    SELECT TYPE, VALUE_ID
    FROM `{TABLE_USER_PREFERENCES}`
    WHERE USER_ID = @user_id
    """

    rows = query_bq(query, {"user_id": user_id})

    return rows


# ============================================================
# ADD PREFERENCE (IDEMPOTENT)
# ============================================================

def add_user_preference(user_id: str, pref_type: str, value_id: str):
    query = f"""
    INSERT INTO `{TABLE_USER_PREFERENCES}` (
        USER_ID,
        TYPE,
        VALUE_ID,
        CREATED_AT
    )
    SELECT
        @user_id,
        @type,
        @value_id,
        CURRENT_TIMESTAMP()
    WHERE NOT EXISTS (
        SELECT 1
        FROM `{TABLE_USER_PREFERENCES}`
        WHERE USER_ID = @user_id
        AND TYPE = @type
        AND VALUE_ID = @value_id
    )
    """

    query_bq(query, {
        "user_id": user_id,
        "type": pref_type,
        "value_id": value_id,
    })


# ============================================================
# REMOVE PREFERENCE
# ============================================================

def remove_user_preference(user_id: str, pref_type: str, value_id: str):
    query = f"""
    DELETE FROM `{TABLE_USER_PREFERENCES}`
    WHERE USER_ID = @user_id
    AND TYPE = @type
    AND VALUE_ID = @value_id
    """

    query_bq(query, {
        "user_id": user_id,
        "type": pref_type,
        "value_id": value_id,
    })


# ============================================================
# GET FORMATTED (OPTIONAL HELPER)
# ============================================================

def get_user_preferences_grouped(user_id: str):
    rows = get_user_preferences(user_id)

    result = {
        "COMPANY": [],
        "SOLUTION": [],
        "TOPIC": [],
    }

    for row in rows:
        result[row["TYPE"]].append(row["VALUE_ID"])

    return result
