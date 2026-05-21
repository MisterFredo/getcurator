# ============================================================
# IMPORTS
# ============================================================

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq
from typing import Dict, List


# ============================================================
# TABLE
# ============================================================

TABLE_USER_PREFERENCES = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_PREFERENCES"
)


# ============================================================
# GET USER PREFERENCES
# ============================================================

def get_user_preferences(user_id: str) -> List[Dict]:
    query = f"""
    SELECT TYPE, VALUE_ID
    FROM `{TABLE_USER_PREFERENCES}`
    WHERE USER_ID = @user_id
    """

    return query_bq(query, {"user_id": user_id}) or []


# ============================================================
# ADD PREFERENCE (IDEMPOTENT - BIGQUERY SAFE)
# ============================================================

def add_user_preference(user_id: str, pref_type: str, value_id: str):

    if not user_id or not pref_type or not value_id:
        return

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

    if not user_id or not pref_type or not value_id:
        return

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
# GET FORMATTED (GROUPED)
# ============================================================

def get_user_preferences_grouped(user_id: str) -> Dict[str, List[str]]:

    rows = get_user_preferences(user_id)

    result = {
        "COMPANY": [],
        "SOLUTION": [],
        "TOPIC": [],
    }

    for row in rows:
        pref_type = row.get("TYPE")
        value_id = row.get("VALUE_ID")

        # 🔥 sécurité : ignore types inconnus
        if pref_type in result and value_id:
            result[pref_type].append(value_id)

    return result
