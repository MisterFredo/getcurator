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
# TABLES
# ============================================================

TABLE_USER_PREFERENCES = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_PREFERENCES"
)

TABLE_COMPANY = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY"
)

TABLE_TOPIC = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOPIC"
)

TABLE_SOLUTION = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION"
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

def get_user_preferences_for_admin(
    user_id: str,
) -> Dict:

    query = f"""
    SELECT
        p.TYPE,
        p.VALUE_ID,

        c.NAME AS COMPANY_NAME,
        t.LABEL AS TOPIC_NAME,
        s.NAME AS SOLUTION_NAME

    FROM `{TABLE_USER_PREFERENCES}` p

    LEFT JOIN `{TABLE_COMPANY}` c
        ON p.TYPE = 'COMPANY'
       AND p.VALUE_ID = c.ID_COMPANY

    LEFT JOIN `{TABLE_TOPIC}` t
        ON p.TYPE = 'TOPIC'
       AND p.VALUE_ID = t.ID_TOPIC

    LEFT JOIN `{TABLE_SOLUTION}` s
        ON p.TYPE = 'SOLUTION'
       AND p.VALUE_ID = s.ID_SOLUTION

    WHERE p.ID_USER = @user_id

    ORDER BY p.TYPE
    """

    rows = (
        query_bq(
            query,
            {
                "user_id": user_id,
            },
        )
        or []
    )

    result = {
        "companies": [],
        "topics": [],
        "solutions": [],
    }

    for row in rows:

        if row["TYPE"] == "COMPANY":

            result["companies"].append(
                {
                    "id": row["VALUE_ID"],
                    "label": row["COMPANY_NAME"],
                }
            )

        elif row["TYPE"] == "TOPIC":

            result["topics"].append(
                {
                    "id": row["VALUE_ID"],
                    "label": row["TOPIC_NAME"],
                }
            )

        elif row["TYPE"] == "SOLUTION":

            result["solutions"].append(
                {
                    "id": row["VALUE_ID"],
                    "label": row["SOLUTION_NAME"],
                }
            )

    return result

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


# =========================================================
# USER PREFERENCES DETAILED
# =========================================================

def get_user_preferences_detailed(
    user_id: str
):

    rows = query_bq(
        f"""
        SELECT
            TYPE,
            VALUE_ID
        FROM `{TABLE_USER_PREFERENCES}`
        WHERE ID_USER = @user_id
        """,
        {
            "user_id": user_id
        }
    )

    result = {
        "COMPANY": [],
        "SOLUTION": [],
        "TOPIC": [],
    }

    if not rows:
        return result

    company_ids = [
        r["VALUE_ID"]
        for r in rows
        if r["TYPE"] == "COMPANY"
    ]

    solution_ids = [
        r["VALUE_ID"]
        for r in rows
        if r["TYPE"] == "SOLUTION"
    ]

    topic_ids = [
        r["VALUE_ID"]
        for r in rows
        if r["TYPE"] == "TOPIC"
    ]

    # =====================================================
    # COMPANIES
    # =====================================================

    if company_ids:

        companies = query_bq(
            f"""
            SELECT
                ID_COMPANY,
                NAME,
                MEDIA_LOGO_RECTANGLE_ID
            FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY`
            WHERE ID_COMPANY IN UNNEST(@ids)
            """,
            {
                "ids": company_ids
            }
        )

        result["COMPANY"] = [
            {
                "id": c["ID_COMPANY"],
                "label": c["NAME"],
                "logo": c.get("MEDIA_LOGO_RECTANGLE_ID"),
            }
            for c in companies
        ]

    # =====================================================
    # SOLUTIONS
    # =====================================================

    if solution_ids:

        solutions = query_bq(
            f"""
            SELECT
                s.ID_SOLUTION,
                s.NAME,
                c.MEDIA_LOGO_RECTANGLE_ID
            FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION` s
            LEFT JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY` c
                ON s.ID_COMPANY = c.ID_COMPANY
            WHERE s.ID_SOLUTION IN UNNEST(@ids)
            """,
            {
                "ids": solution_ids
            }
        )

        result["SOLUTION"] = [
            {
                "id": s["ID_SOLUTION"],
                "label": s["NAME"],
                "logo": s.get("MEDIA_LOGO_RECTANGLE_ID"),
            }
            for s in solutions
        ]

    # =====================================================
    # TOPICS
    # =====================================================

    if topic_ids:

        topics = query_bq(
            f"""
            SELECT
                ID_TOPIC,
                LABEL
            FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOPIC`
            WHERE ID_TOPIC IN UNNEST(@ids)
            """,
            {
                "ids": topic_ids
            }
        )

        result["TOPIC"] = [
            {
                "id": t["ID_TOPIC"],
                "label": t["LABEL"],
            }
            for t in topics
        ]

    return result


# ============================================================
# REPLACE USER PREFERENCES
# ============================================================

def set_user_preferences(
    user_id: str,
    companies: List[str],
    solutions: List[str],
    topics: List[str],
):

    if not user_id:
        return

    # ========================================================
    # CLEAR EXISTING PREFERENCES
    # ========================================================

    query_bq(
        f"""
        DELETE FROM `{TABLE_USER_PREFERENCES}`
        WHERE ID_USER = @user_id
        """,
        {
            "user_id": user_id,
        },
    )

    # ========================================================
    # COMPANIES
    # ========================================================

    for company_id in companies or []:

        add_user_preference(
            user_id=user_id,
            pref_type="COMPANY",
            value_id=company_id,
        )

    # ========================================================
    # SOLUTIONS
    # ========================================================

    for solution_id in solutions or []:

        add_user_preference(
            user_id=user_id,
            pref_type="SOLUTION",
            value_id=solution_id,
        )

    # ========================================================
    # TOPICS
    # ========================================================

    for topic_id in topics or []:

        add_user_preference(
            user_id=user_id,
            pref_type="TOPIC",
            value_id=topic_id,
        )
