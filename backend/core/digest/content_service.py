# backend/core/digest/content_service.py

from typing import (
    Dict,
    Any,
    List,
)

from utils.bigquery_utils import (
    query_bq,
)

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from core.curator.entity_service import (
    get_company_feed,
    get_solution_feed,
    get_topic_feed,
)

# ============================================================
# TABLES
# ============================================================

TABLE_USER_PREFERENCES = f"""
{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_PREFERENCES
"""

# ============================================================
# LOAD USER PREFERENCES
# ============================================================

def load_user_preferences(
    user_id: str,
) -> Dict[str, List[str]]:

    sql = f"""

    SELECT
        TYPE,
        VALUE_ID

    FROM `{TABLE_USER_PREFERENCES}`

    WHERE ID_USER = @user_id

    """

    rows = query_bq(
        sql,

        params={
            "user_id": user_id,
        },
    )

    company_ids = []
    solution_ids = []
    topic_ids = []

    for row in rows:

        pref_type = (
            row.get("TYPE")
            or ""
        ).upper()

        value_id = row.get(
            "VALUE_ID"
        )

        if not value_id:
            continue

        # ====================================================
        # COMPANY
        # ====================================================

        if pref_type == "COMPANY":

            company_ids.append(
                value_id
            )

        # ====================================================
        # SOLUTION
        # ====================================================

        elif pref_type == "SOLUTION":

            solution_ids.append(
                value_id
            )

        # ====================================================
        # TOPIC
        # ====================================================

        elif pref_type == "TOPIC":

            topic_ids.append(
                value_id
            )

    return {
        "companies":
            company_ids,

        "solutions":
            solution_ids,

        "topics":
            topic_ids,
    }

# ============================================================
# DIGEST CONTENTS
# ============================================================

def get_digest_contents(
    user_id: str,

    limit: int = 50,
) -> Dict[str, Any]:

    # ========================================================
    # LOAD USER PREFS
    # ========================================================

    prefs = load_user_preferences(
        user_id
    )

    company_ids = prefs[
        "companies"
    ]

    solution_ids = prefs[
        "solutions"
    ]

    topic_ids = prefs[
        "topics"
    ]

    # ========================================================
    # LOAD FEEDS
    # ========================================================

    all_contents = []

    # ========================================================
    # COMPANY FEEDS
    # ========================================================

    for company_id in company_ids:

        try:

            items = (
                get_company_feed(
                    company_id=
                        company_id,

                    limit=limit,
                )
            )

            if items:

                all_contents.extend(
                    items
                )

        except Exception as e:

            print(
                "Digest company feed error:",
                company_id,
                e,
            )

    # ========================================================
    # SOLUTION FEEDS
    # ========================================================

    for solution_id in solution_ids:

        try:

            items = (
                get_solution_feed(
                    solution_id=
                        solution_id,

                    limit=limit,
                )
            )

            if items:

                all_contents.extend(
                    items
                )

        except Exception as e:

            print(
                "Digest solution feed error:",
                solution_id,
                e,
            )

    # ========================================================
    # TOPIC FEEDS
    # ========================================================

    for topic_id in topic_ids:

        try:

            items = (
                get_topic_feed(
                    topic_id=
                        topic_id,

                    limit=limit,
                )
            )

            if items:

                all_contents.extend(
                    items
                )

        except Exception as e:

            print(
                "Digest topic feed error:",
                topic_id,
                e,
            )

    # ========================================================
    # DEDUPE
    # ========================================================

    deduped = {}

    for item in all_contents:

        content_id = (
            item.get("id")
            or item.get("ID_CONTENT")
            or item.get("id_content")
        )

        if not content_id:
            continue

        existing = deduped.get(
            content_id
        )

        # ====================================================
        # KEEP MOST RECENT
        # ====================================================

        if not existing:

            deduped[
                content_id
            ] = item

    # ========================================================
    # SORT
    # ========================================================

    final_contents = sorted(
        deduped.values(),

        key=lambda x:
            x.get(
                "published_at"
            )
            or "",

        reverse=True,
    )

    # ========================================================
    # LIMIT
    # ========================================================

    final_contents = (
        final_contents[:limit]
    )

    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "contents":
            final_contents,

        "preferences": {
            "companies":
                company_ids,

            "solutions":
                solution_ids,

            "topics":
                topic_ids,
        },
    }
