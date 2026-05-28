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

    print("LOAD USER")
    print(rows)

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

    print("USER PREFS ROWS")
    print(rows)

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

        print("PREF ROW")
        print(pref_type)
        print(value_id)

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

    result = {
        "companies":
            company_ids,

        "solutions":
            solution_ids,

        "topics":
            topic_ids,
    }

    print("USER PREFS RESULT")
    print(result)

    return result

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

    print("LAST SENT")
    print(rows)

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

    if not filters:

        print("NO FILTERS")
        return "1 = 0"

    result = " OR ".join(
        filters
    )

    print("FILTER SQL")
    print(result)

    return result

# ============================================================
# DIGEST CONTENTS
# ============================================================

def get_digest_contents(
    user_id: str,

    limit: int = 50,
) -> Dict[str, Any]:

    print("===================================")
    print("DIGEST START")
    print(user_id)
    print("===================================")

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

    print("LANGUAGE")
    print(language)

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

    print("COMPANY IDS")
    print(company_ids)

    print("SOLUTION IDS")
    print(solution_ids)

    print("TOPIC IDS")
    print(topic_ids)

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

        TITLE_EN,
        EXCERPT_EN

    FROM `{TABLE_CONTENT_ENRICHED}`

    WHERE
        is_active = TRUE

        AND status = "PUBLISHED"

        AND (
            {filters_sql}
        )

    ORDER BY
        published_at DESC

    LIMIT {limit}

    """

    print("========== DIGEST SQL ==========")
    print(sql)
    print("================================")

    rows = query_bq(
        sql
    )

    print("ROWS COUNT")
    print(len(rows))

    if rows:
        print("FIRST ROW")
        print(rows[0])

    # ========================================================
    # NORMALIZE
    # ========================================================

    contents = []

    for row in rows:

        try:

            companies = (
                row.get("companies")
                or []
            )

            primary_logo = None

            primary_company_id = (
                row.get(
                    "ID_PRIMARY_COMPANY"
                )
            )

            if (
                primary_company_id
                and companies
            ):

                for company in companies:

                    if (
                        company.get(
                            "id_company"
                        )
                        == primary_company_id
                    ):

                        primary_logo = (
                            company.get(
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

                "url":
                    f"https://www.getcurator.ai/content/{row.get('id')}",

                "primary_company_logo":
                    primary_logo,

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

            print("CONTENT BUILT")
            print(content)

            contents.append(
                content
            )

        except Exception as e:

            print("CONTENT BUILD ERROR")
            print(e)

    print("FINAL CONTENTS COUNT")
    print(len(contents))

    # ========================================================
    # LAST SENT
    # ========================================================

    last_sent_at = (
        get_last_digest_sent(
            user_id
        )
    )

    print("FINAL RESPONSE")
    print({
        "contents_count": len(contents),
        "language": language,
        "last_sent_at": last_sent_at,
    })

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
