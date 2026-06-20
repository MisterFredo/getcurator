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

from core.user.user_keyword_service import (
    get_user_keywords,
)

from core.user.user_profile_service import (
    get_user_profile,
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
# USER CONTEXT
# ============================================================

def load_user_context(
    user_id: str,
) -> Dict[str, Any]:

    user = load_user(
        user_id
    )

    preferences = (
        load_user_preferences(
            user_id
        )
    )

    keywords = (
        get_user_keywords(
            user_id
        )
        or []
    )

    profile = (
        get_user_profile(
            user_id
        )
        or {}
    )

    geographies = [
        g
        for g in [
            profile.get(
                "geography_1"
            ),
            profile.get(
                "geography_2"
            ),
            profile.get(
                "geography_3"
            ),
        ]
        if g
    ]

    return {
        "user": user,

        "preferences":
            preferences,

        "keywords":
            keywords,

        "geographies":
            geographies,

        "profile_text":
            profile.get(
                "profile_text"
            ),
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
# KEYWORDS FILTER
# ============================================================

def build_keywords_filter(
    keywords: List[str],
) -> str:

    if not keywords:
        return ""

    conditions = []

    for keyword in keywords:

        keyword = (
            keyword or ""
        ).strip()

        if not keyword:
            continue

        keyword = (
            keyword
            .replace("'", "\\'")
        )

        conditions.append(
            f"""

            LOWER(
                COALESCE(title, '')
            ) LIKE LOWER('%{keyword}%')

            OR LOWER(
                COALESCE(TITLE_EN, '')
            ) LIKE LOWER('%{keyword}%')

            OR LOWER(
                COALESCE(excerpt, '')
            ) LIKE LOWER('%{keyword}%')

            OR LOWER(
                COALESCE(EXCERPT_EN, '')
            ) LIKE LOWER('%{keyword}%')

            OR LOWER(
                COALESCE(content_body, '')
            ) LIKE LOWER('%{keyword}%')

            OR LOWER(
                COALESCE(signal_analytique, '')
            ) LIKE LOWER('%{keyword}%')

            OR LOWER(
                COALESCE(mecanique_expliquee, '')
            ) LIKE LOWER('%{keyword}%')

            OR LOWER(
                COALESCE(enjeu_strategique, '')
            ) LIKE LOWER('%{keyword}%')

            OR LOWER(
                COALESCE(point_de_friction, '')
            ) LIKE LOWER('%{keyword}%')

            """
        )

    if not conditions:
        return ""

    return (
        "("
        + " OR ".join(
            conditions
        )
        + ")"
    )

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
    # USER CONTEXT
    # ========================================================

    context = load_user_context(
        user_id
    )

    user = (
        context.get("user")
        or {}
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

    prefs = (
        context.get(
            "preferences"
        )
        or {}
    )

    company_ids = (
        prefs.get(
            "companies"
        )
        or []
    )

    solution_ids = (
        prefs.get(
            "solutions"
        )
        or []
    )

    topic_ids = (
        prefs.get(
            "topics"
        )
        or []
    )

    keywords = (
        context.get(
            "keywords"
        )
        or []
    )

    geographies = (
        context.get(
            "geographies"
        )
        or []
    )

    profile_text = (
        context.get(
            "profile_text"
        )
    )

    print("COMPANY IDS")
    print(company_ids)

    print("SOLUTION IDS")
    print(solution_ids)

    print("TOPIC IDS")
    print(topic_ids)

    print("KEYWORDS")
    print(keywords)

    print("GEOGRAPHIES")
    print(geographies)

    print("PROFILE TEXT")
    print(profile_text)

    # ========================================================
    # FILTERS
    # ========================================================

    filters_sql = build_filters(
        company_ids=company_ids,
        solution_ids=solution_ids,
        topic_ids=topic_ids,
    )

    keywords_sql = build_keywords_filter(
        keywords
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

            (
                {filters_sql}
            )

            OR

            (
                {keywords_sql}
            )

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
                    (
                        f"https://www.getcurator.ai/feed?news_id={row.get('id')}"
                        if (
                            row.get("content_type")
                            or ""
                        ).upper() == "NEWS"
                        else
                        f"https://www.getcurator.ai/feed?analysis_id={row.get('id')}"
                    ),

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
        "keywords": len(keywords),
        "geographies": len(geographies),
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

        "user_context": {

            "keywords":
                keywords,

            "geographies":
                geographies,

            "profile_text":
                profile_text,
        },

        "language":
            language,

        "last_sent_at":
            last_sent_at,
    }
