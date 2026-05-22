# ============================================================
# IMPORTS
# ============================================================

from typing import (
    Dict,
    List,
)

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
)


# ============================================================
# TABLE
# ============================================================

TABLE_USER_PREFERENCES = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_PREFERENCES"
)


# ============================================================
# GET USER PREFERENCES
# ============================================================

def get_user_preferences(
    user_id: str
) -> List[Dict]:

    query = f"""
    SELECT
        TYPE,
        VALUE_ID

    FROM `{TABLE_USER_PREFERENCES}`

    WHERE ID_USER = @user_id
    """

    return (
        query_bq(
            query,
            {
                "user_id": user_id
            }
        )
        or []
    )


# ============================================================
# ADD PREFERENCE
# ============================================================

def add_user_preference(
    user_id: str,
    pref_type: str,
    value_id: str,
):

    if (
        not user_id
        or not pref_type
        or not value_id
    ):
        return

    query = f"""
    MERGE `{TABLE_USER_PREFERENCES}` T

    USING (
        SELECT
            @user_id AS ID_USER,
            @type AS TYPE,
            @value_id AS VALUE_ID
    ) S

    ON T.ID_USER = S.ID_USER
       AND T.TYPE = S.TYPE
       AND T.VALUE_ID = S.VALUE_ID

    WHEN NOT MATCHED THEN

      INSERT (
        ID_USER,
        TYPE,
        VALUE_ID,
        CREATED_AT,
        UPDATED_AT
      )

      VALUES (
        S.ID_USER,
        S.TYPE,
        S.VALUE_ID,
        CURRENT_TIMESTAMP(),
        CURRENT_TIMESTAMP()
      )
    """

    query_bq(
        query,
        {
            "user_id": user_id,
            "type": pref_type,
            "value_id": value_id,
        }
    )


# ============================================================
# REMOVE PREFERENCE
# ============================================================

def remove_user_preference(
    user_id: str,
    pref_type: str,
    value_id: str,
):

    if (
        not user_id
        or not pref_type
        or not value_id
    ):
        return

    query = f"""
    DELETE FROM `{TABLE_USER_PREFERENCES}`

    WHERE ID_USER = @user_id
      AND TYPE = @type
      AND VALUE_ID = @value_id
    """

    query_bq(
        query,
        {
            "user_id": user_id,
            "type": pref_type,
            "value_id": value_id,
        }
    )


# ============================================================
# GET FORMATTED (GROUPED)
# ============================================================

def get_user_preferences_grouped(
    user_id: str
) -> Dict[str, List[str]]:

    rows = get_user_preferences(user_id)

    result = {
        "COMPANY": [],
        "SOLUTION": [],
        "TOPIC": [],
    }

    for row in rows:

        pref_type = row.get("TYPE")

        value_id = row.get("VALUE_ID")

        # ------------------------------------------------------
        # SAFETY
        # ------------------------------------------------------

        if (
            pref_type in result
            and value_id
        ):

            result[pref_type].append(
                value_id
            )

    return result
