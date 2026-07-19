from typing import List, Dict

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
)

# =========================================================
# TABLE
# =========================================================

TABLE_USER_EXPERT = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_EXPERT"
)

TABLE_USER = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER"
)

# =========================================================
# SUBSCRIBE
# =========================================================

def subscribe_user_to_expert(
    user_id: str,
    expert_id: str,
):

    if not user_id or not expert_id:
        return

    query = f"""
    MERGE `{TABLE_USER_EXPERT}` T

    USING (

        SELECT
            @user_id AS ID_USER,
            @expert_id AS ID_EXPERT

    ) S

    ON
        T.ID_USER = S.ID_USER
    AND
        T.ID_EXPERT = S.ID_EXPERT

    WHEN NOT MATCHED THEN

        INSERT (
            ID_USER,
            ID_EXPERT,
            CREATED_AT
        )

        VALUES (
            S.ID_USER,
            S.ID_EXPERT,
            CURRENT_TIMESTAMP()
        )
    """

    query_bq(
        query,
        {
            "user_id": user_id,
            "expert_id": expert_id,
        },
    )


# =========================================================
# UNSUBSCRIBE
# =========================================================

def unsubscribe_user_from_expert(
    user_id: str,
    expert_id: str,
):

    query = f"""
    DELETE
    FROM `{TABLE_USER_EXPERT}`

    WHERE
        ID_USER = @user_id
    AND
        ID_EXPERT = @expert_id
    """

    query_bq(
        query,
        {
            "user_id": user_id,
            "expert_id": expert_id,
        },
    )


# =========================================================
# USER -> EXPERTS
# =========================================================

def get_user_experts(
    user_id: str,
) -> List[Dict]:

    query = f"""

    SELECT

        u.ID_USER,
        u.DISPLAY_NAME,
        u.NAME,
        u.DESCRIPTION,
        u.FREQUENCY

    FROM `{TABLE_USER_EXPERT}` ue

    JOIN `{TABLE_USER}` u

        ON ue.ID_EXPERT = u.ID_USER

    WHERE

        ue.ID_USER = @user_id

    ORDER BY
        u.DISPLAY_NAME,
        u.NAME

    """

    return query_bq(
        query,
        {
            "user_id": user_id,
        },
    ) or []


# =========================================================
# EXPERT -> USERS
# =========================================================

def get_expert_users(
    expert_id: str,
) -> List[Dict]:

    query = f"""

    SELECT

        u.ID_USER,
        u.NAME,
        u.EMAIL,
        u.COMPANY

    FROM `{TABLE_USER_EXPERT}` ue

    JOIN `{TABLE_USER}` u

        ON ue.ID_USER = u.ID_USER

    WHERE

        ue.ID_EXPERT = @expert_id

    ORDER BY
        u.NAME

    """

    return query_bq(
        query,
        {
            "expert_id": expert_id,
        },
    ) or []
