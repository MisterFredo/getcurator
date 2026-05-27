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

# ============================================================
# TABLES
# ============================================================

TABLE_USER = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER"
)

TABLE_USER_PREFERENCES = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_PREFERENCES"
)

TABLE_DIGEST_SEND = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_DIGEST_SEND"
)

TABLE_CONTENT_ENRICHED = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_ENRICHED"
)

# ============================================================
# LOAD USER
# ============================================================

def load_user(
    user_id: str,
) -> Dict[str, Any]:

    sql = f"""

    SELECT
        ID_USER,
        EMAIL,
        NAME,
        COMPANY,
        LANGUAGE

    FROM `{TABLE_USER}`

    WHERE ID_USER = @user_id

    LIMIT 1

    """

    rows = query_bq(
        sql,

        params={
            "user_id": user_id,
        },
    )

    if not rows:
        return {}

    return rows[0]

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
# LAST DIGEST SENT
# ============================================================

def get_last_digest_sent(
    user_id: str,
):

    sql = f"""

    SELECT
        MAX(SENT_AT) AS LAST_SENT_AT

    FROM `{TABLE_DIGEST_SEND}`

    WHERE ID_USER = @user_id

    """

    rows = query_bq(
        sql,

        params={
            "user_id": user_id,
        },
    )

    if not rows:
        return None

    return rows[0].get(
        "LAST_SENT_AT"
    )

# ============================================================
# BUILD FILTERS
# ============================================================

def build_filters(
    company_ids: List[str],
    solution_ids: List[str],
    topic_ids: List[str],
) -> str:

    filters = []

    # ========================================================
    # COMPANIES
    # ========================================================

    if company_ids:

        company_list = ",".join(
            [
                f"'{x}'"
                for x in company_ids
            ]
        )

        filters.append(
            f"""

            EXISTS (

                SELECT 1

                FROM UNNEST(companies) c

                WHERE c.id_company IN (
                    {company_list}
                )

            )

            """
        )

    # ========================================================
    # SOLUTIONS
    # ========================================================

    if solution_ids:

        solution_list = ",".join(
            [
                f"'{x}'"
                for x in solution_ids
            ]
        )

        filters.append(
            f"""

            EXISTS (

                SELECT 1

                FROM UNNEST(solutions) s

                WHERE s.id_solution IN (
                    {solution_list}
                )

            )

            """
        )

    # ========================================================
    # TOPICS
    # ========================================================

    if topic_ids:

        topic_list = ",".join(
            [
                f"'{x}'"
                for x in topic_ids
            ]
        )

        filters.append(
            f"""

            EXISTS (

                SELECT 1

                FROM UNNEST(topics) t

                WHERE t.id_topic IN (
                    {topic_list}
                )

            )

            """
        )

    # ========================================================
    # EMPTY
    # ========================================================

    if not filters:

        return "1 = 0"

    return " OR ".join(
        filters
    )

# ============================================================
# DIGEST CONTENTS
# ============================================================

def get_digest_contents(
    user_id: str,

    limit: int = 50,
) -> Dict[str, Any]:

    # ========================================================
    # USER
    # ========================================================

    user = load_user(
        user_id
    )

    language = (
        user.get("LANGUAGE")
        or "fr"
    ).lower()

    is_en = (
        language == "en"
    )

    # ========================================================
    # USER PREFS
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
    # FILTERS
    # ========================================================

    filters_sql = build_filters(
        company_ids=
            company_ids,

        solution_ids=
            solution_ids,

        topic_ids=
            topic_ids,
    )

    # ========================================================
    # TITLE / EXCERPT
    # ========================================================

    if is_en:

        title_sql = """

        COALESCE(
            TITLE_EN,
            title
        ) AS title

        """

        excerpt_sql = """

        COALESCE(
            EXCERPT_EN,
            excerpt
        ) AS excerpt

        """

    else:

        title_sql = """
        title AS title
        """

        excerpt_sql = """
        excerpt AS excerpt
        """

    # ========================================================
    # QUERY
    # ========================================================

    sql = f"""

    SELECT

        id_content AS id,

        CONTENT_TYPE AS content_type,

        {title_sql},

        {excerpt_sql},

        published_at,

        source_url,

        source_title,

        source_id,

        ID_PRIMARY_COMPANY,

        companies,

        solutions,

        topics,

        universes,

        concepts,

        media_id,

        TITLE_EN,
        EXCERPT_EN

    FROM `{TABLE_CONTENT_ENRICHED}`

    WHERE
        is_active = TRUE

        AND status = "published"

        AND (
            {filters_sql}
        )

    ORDER BY
        published_at DESC

    LIMIT {limit}

    """

    rows = query_bq(
        sql
    )

    # ========================================================
    # NORMALIZE
    # ========================================================

    contents = []

    for row in rows:

        companies = (
            row.get("companies")
            or []
        )

        primary_logo = None

        if companies:

            first_company = (
                companies[0]
            )

            primary_logo = (
                first_company.get(
                    "media_logo_rectangle_id"
                )
            )

        content = {
            "id":
                row.get("id"),

            "content_type":
                (
                    row.get(
                        "content_type"
                    )
                    or "analysis"
                ).lower(),

            "title":
                row.get(
                    "title"
                ),

            "excerpt":
                row.get(
                    "excerpt"
                ),

            "published_at":
                row.get(
                    "published_at"
                ),

            # =================================================
            # GETCURATOR URL
            # =================================================

            "url":
                f"https://www.getcurator.ai/content/{row.get('id')}",

            # =================================================
            # VISUALS
            # =================================================

            "media_id":
                row.get(
                    "media_id"
                ),

            "primary_company_logo":
                primary_logo,

            # =================================================
            # ENTITIES
            # =================================================

            "companies":
                companies,

            "solutions":
                row.get(
                    "solutions"
                )
                or [],

            "topics":
                row.get(
                    "topics"
                )
                or [],

            "universes":
                row.get(
                    "universes"
                )
                or [],

            "concepts":
                row.get(
                    "concepts"
                )
                or [],
        }

        contents.append(
            content
        )

    # ========================================================
    # LAST SENT
    # ========================================================

    last_sent_at = (
        get_last_digest_sent(
            user_id
        )
    )

    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "contents":
            contents,

        "preferences": {
            "companies":
                company_ids,

            "solutions":
                solution_ids,

            "topics":
                topic_ids,
        },

        "language":
            language,

        "last_sent_at":
            last_sent_at,
    }
