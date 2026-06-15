from typing import List, Dict

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
    insert_bq,
)

TABLE_USER_KEYWORD = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_KEYWORD"
)

# =========================================================
# GET USER KEYWORDS
# =========================================================

def get_user_keywords(
    user_id: str
) -> List[str]:

    rows = query_bq(
        f"""
        SELECT
            KEYWORD
        FROM `{TABLE_USER_KEYWORD}`
        WHERE ID_USER = @user_id
        ORDER BY KEYWORD
        """,
        {
            "user_id": user_id
        }
    )

    return [
        row["KEYWORD"]
        for row in rows
        if row.get("KEYWORD")
    ]

# =========================================================
# ADD USER KEYWORD
# =========================================================

def add_user_keyword(
    user_id: str,
    keyword: str,
):

    keyword = (
        keyword or ""
    ).strip()

    if not keyword:
        return

    existing = query_bq(
        f"""
        SELECT 1
        FROM `{TABLE_USER_KEYWORD}`
        WHERE ID_USER = @user_id
          AND LOWER(KEYWORD) = LOWER(@keyword)
        LIMIT 1
        """,
        {
            "user_id": user_id,
            "keyword": keyword,
        }
    )

    if existing:
        return

    insert_bq(
        TABLE_USER_KEYWORD,
        [
            {
                "ID_USER": user_id,
                "KEYWORD": keyword,
            }
        ]
    )

# =========================================================
# REMOVE USER KEYWORD
# =========================================================

def remove_user_keyword(
    user_id: str,
    keyword: str,
):

    query_bq(
        f"""
        DELETE
        FROM `{TABLE_USER_KEYWORD}`
        WHERE ID_USER = @user_id
          AND LOWER(KEYWORD) = LOWER(@keyword)
        """,
        {
            "user_id": user_id,
            "keyword": keyword,
        }
    )
