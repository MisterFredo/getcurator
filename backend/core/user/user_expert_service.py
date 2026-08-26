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


# =========================================================
# TABLES
# =========================================================

TABLE_USER_EXPERT = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_EXPERT"
)

TABLE_USER = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER"
)

TABLE_USER_UNIVERSE = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_UNIVERSE"
)


# =========================================================
# CHECK ELIGIBILITY
# =========================================================

def can_user_subscribe_to_expert(
    user_id: str,
    expert_id: str,
) -> bool:

    if not user_id or not expert_id:

        return False

    rows = query_bq(
        f"""
        SELECT 1

        FROM `{TABLE_USER}` expert

        WHERE

            expert.ID_USER = @expert_id

            AND expert.PROFILE_TYPE = "EXPERT"

            AND expert.IS_ACTIVE = TRUE

            AND EXISTS (

                SELECT 1

                FROM `{TABLE_USER_UNIVERSE}` user_universe

                JOIN `{TABLE_USER_UNIVERSE}` expert_universe

                    ON
                        expert_universe.ID_UNIVERSE =
                        user_universe.ID_UNIVERSE

                WHERE

                    user_universe.ID_USER =
                        @user_id

                    AND expert_universe.ID_USER =
                        @expert_id

            )

        LIMIT 1
        """,
        {
            "user_id":
                user_id,

            "expert_id":
                expert_id,
        },
    )

    return bool(
        rows
    )


# =========================================================
# SUBSCRIBE
# =========================================================

def subscribe_user_to_expert(
    user_id: str,
    expert_id: str,
):

    if not user_id or not expert_id:

        raise ValueError(
            "User and expert are required"
        )

    if not can_user_subscribe_to_expert(

        user_id=user_id,

        expert_id=expert_id,

    ):

        raise ValueError(
            "This expert does not belong "
            "to any of the user's universes"
        )

    query = f"""
    MERGE `{TABLE_USER_EXPERT}` T

    USING (

        SELECT

            @user_id AS ID_USER,

            @expert_id AS ID_EXPERT

    ) S

    ON

        T.ID_USER = S.ID_USER

        AND T.ID_EXPERT =
            S.ID_EXPERT

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
            "user_id":
                user_id,

            "expert_id":
                expert_id,
        },
    )

    return {
        "status": "ok",
        "user_id": user_id,
        "expert_id": expert_id,
    }


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

        AND ID_EXPERT =
            @expert_id
    """

    query_bq(
        query,
        {
            "user_id":
                user_id,

            "expert_id":
                expert_id,
        },
    )

    return {
        "status": "ok",
        "user_id": user_id,
        "expert_id": expert_id,
    }


# =========================================================
# USER -> AVAILABLE EXPERTS
# =========================================================

def get_user_experts(
    user_id: str,
) -> List[Dict]:

    query = f"""

    SELECT

        expert.ID_USER,

        expert.DISPLAY_NAME,

        expert.NAME,

        expert.DESCRIPTION,

        expert.IS_ACTIVE,

        EXISTS (

            SELECT 1

            FROM `{TABLE_USER_EXPERT}` selected

            WHERE

                selected.ID_EXPERT =
                    expert.ID_USER

                AND selected.ID_USER =
                    @user_id

        ) AS IS_SELECTED,

        (

            SELECT

                COUNT(
                    DISTINCT subscription.ID_USER
                )

            FROM `{TABLE_USER_EXPERT}` subscription

            WHERE

                subscription.ID_EXPERT =
                    expert.ID_USER

        ) AS USER_COUNT

    FROM `{TABLE_USER}` expert

    WHERE

        expert.PROFILE_TYPE = "EXPERT"

        AND expert.IS_ACTIVE = TRUE

        AND EXISTS (

            SELECT 1

            FROM `{TABLE_USER_UNIVERSE}` user_universe

            JOIN `{TABLE_USER_UNIVERSE}` expert_universe

                ON
                    expert_universe.ID_UNIVERSE =
                    user_universe.ID_UNIVERSE

            WHERE

                user_universe.ID_USER =
                    @user_id

                AND expert_universe.ID_USER =
                    expert.ID_USER

        )

    ORDER BY

        IS_SELECTED DESC,

        expert.DISPLAY_NAME,

        expert.NAME

    """

    return query_bq(
        query,
        {
            "user_id":
                user_id,
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

        user.ID_USER,

        user.NAME,

        user.EMAIL,

        user.COMPANY

    FROM `{TABLE_USER_EXPERT}` subscription

    JOIN `{TABLE_USER}` user

        ON
            subscription.ID_USER =
            user.ID_USER

    WHERE

        subscription.ID_EXPERT =
            @expert_id

    ORDER BY

        user.NAME

    """

    return query_bq(
        query,
        {
            "expert_id":
                expert_id,
        },
    ) or []


# =========================================================
# CHECK USER -> EXPERT
# =========================================================

def is_user_subscribed_to_expert(
    user_id: str,
    expert_id: str,
) -> bool:

    if not user_id or not expert_id:

        return False

    rows = query_bq(
        f"""
        SELECT 1

        FROM `{TABLE_USER_EXPERT}`

        WHERE

            ID_USER = @user_id

            AND ID_EXPERT =
                @expert_id

        LIMIT 1
        """,
        {
            "user_id":
                user_id,

            "expert_id":
                expert_id,
        },
    )

    return bool(
        rows
    )


# =========================================================
# REMOVE INCOMPATIBLE EXPERT LINKS
# =========================================================

def remove_incompatible_expert_links(
    changed_user_id: str,
):

    if not changed_user_id:

        return {
            "status": "ok",
            "removed": 0,
        }

    incompatible_sql = f"""

        (

            subscription.ID_USER =
                @changed_user_id

            OR subscription.ID_EXPERT =
                @changed_user_id

        )

        AND NOT EXISTS (

            SELECT 1

            FROM `{TABLE_USER_UNIVERSE}` subscriber_universe

            JOIN `{TABLE_USER_UNIVERSE}` expert_universe

                ON
                    expert_universe.ID_UNIVERSE =
                    subscriber_universe.ID_UNIVERSE

            WHERE

                subscriber_universe.ID_USER =
                    subscription.ID_USER

                AND expert_universe.ID_USER =
                    subscription.ID_EXPERT

        )

    """

    count_rows = query_bq(
        f"""
        SELECT

            COUNT(*) AS total

        FROM `{TABLE_USER_EXPERT}` subscription

        WHERE

            {incompatible_sql}
        """,
        {
            "changed_user_id":
                changed_user_id,
        },
    )

    removed = (

        int(
            count_rows[0].get(
                "total",
                0,
            )
        )

        if count_rows

        else 0

    )

    if removed > 0:

        query_bq(
            f"""
            DELETE
            FROM `{TABLE_USER_EXPERT}` subscription

            WHERE

                {incompatible_sql}
            """,
            {
                "changed_user_id":
                    changed_user_id,
            },
        )

    return {
        "status": "ok",
        "removed": removed,
    }
