# backend/core/expertise/query_builder.py

from api.expertise.models import (
    ExpertiseProfile,
    SelectionFilters,
)

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

TABLE_CONTENT_ENRICHED = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_ENRICHED"
)


# ============================================================
# BUILD SELECTION QUERY
# ============================================================

def build_selection_query(
    profile: ExpertiseProfile,
    period_start: str | None = None,
    period_end: str | None = None,
    limit: int | None = None,
) -> tuple[str, dict]:

    selection = build_selection_filters(
        profile
    )

    params: dict = {

        "company_ids": (
            profile.preferences.companies
        ),

        "solution_ids": (
            profile.preferences.solutions
        ),

        "topic_ids": (
            profile.preferences.topics
        ),

    }

    date_filter_sql = ""

    if period_start:

        date_filter_sql += """

        AND published_at >= @period_start

        """

        params["period_start"] = (
            period_start
        )

    if period_end:

        date_filter_sql += """

        AND published_at < @period_end

        """

        params["period_end"] = (
            period_end
        )

    limit_sql = ""

    if limit:

        limit_sql = f"""

        LIMIT {limit}

        """

    if profile.language == "en":

        title_sql = """

        COALESCE(
            TITLE_EN,
            TITLE
        ) AS title

        """

        excerpt_sql = """

        COALESCE(
            EXCERPT_EN,
            EXCERPT
        ) AS excerpt

        """

    else:

        title_sql = """

        TITLE AS title

        """

        excerpt_sql = """

        EXCERPT AS excerpt

        """

    sql = f"""

    SELECT

        ID_CONTENT AS id,

        {title_sql},

        {excerpt_sql},

        PUBLISHED_AT AS published_at,

        SOURCE_URL AS source_url,

        SOURCE_TITLE AS source_title,

        SOURCE_ID AS source_id,

        ID_PRIMARY_COMPANY,

        CONTENT_BODY AS content_body,

        SIGNAL_ANALYTIQUE AS signal_analytique,

        MECANIQUE_EXPLIQUEE AS mecanique_expliquee,

        ENJEU_STRATEGIQUE AS enjeu_strategique,

        POINT_DE_FRICTION AS point_de_friction,

        CHIFFRES AS chiffres,

        COMPANIES AS companies,

        SOLUTIONS AS solutions,

        TOPICS AS topics,

        UNIVERSES AS universes,

        CONCEPTS AS concepts

    FROM `{TABLE_CONTENT_ENRICHED}`

    WHERE

        IS_ACTIVE = TRUE

        AND STATUS = "PUBLISHED"

        {date_filter_sql}

        AND (

            ({selection.filters_sql})

            OR

            ({selection.keywords_sql})

        )

    ORDER BY

        PUBLISHED_AT DESC

    {limit_sql}

    """

    return sql, params


# ============================================================
# BUILD SELECTION FILTERS
# ============================================================

def build_selection_filters(
    profile: ExpertiseProfile,
) -> SelectionFilters:

    filters_sql = build_filters_sql(

        company_ids=profile.preferences.companies,

        solution_ids=profile.preferences.solutions,

        topic_ids=profile.preferences.topics,

    )

    keywords_sql = build_keywords_sql(
        profile.keywords
    )

    if not keywords_sql:

        keywords_sql = "FALSE"

    return SelectionFilters(

        filters_sql=filters_sql,

        keywords_sql=keywords_sql,

    )

# ============================================================
# BUILD FILTERS SQL
# ============================================================

def build_filters_sql(
    company_ids: list[str],
    solution_ids: list[str],
    topic_ids: list[str],
) -> str:

    filters = []

    if company_ids:

        filters.append(
            """
            EXISTS (
                SELECT 1
                FROM UNNEST(companies) c
                WHERE c.id_company IN UNNEST(@company_ids)
            )
            """
        )

    if solution_ids:

        filters.append(
            """
            EXISTS (
                SELECT 1
                FROM UNNEST(solutions) s
                WHERE s.id_solution IN UNNEST(@solution_ids)
            )
            """
        )

    if topic_ids:

        filters.append(
            """
            EXISTS (
                SELECT 1
                FROM UNNEST(topics) t
                WHERE t.id_topic IN UNNEST(@topic_ids)
            )
            """
        )

    if not filters:

        return "1 = 0"

    return " OR ".join(filters)


# ============================================================
# BUILD KEYWORDS SQL
# ============================================================

def build_keywords_sql(
    keywords: list[str],
) -> str:

    if not keywords:

        return ""

    conditions = []

    fields = [

        "title",

        "TITLE_EN",

        "excerpt",

        "EXCERPT_EN",

        "content_body",

        "signal_analytique",

        "mecanique_expliquee",

        "enjeu_strategique",

        "point_de_friction",

    ]

    for keyword in keywords:

        keyword = (
            keyword
            .strip()
            .replace("'", "\\'")
        )

        if not keyword:

            continue

        field_conditions = [

            f"LOWER(COALESCE({field}, '')) LIKE LOWER('%{keyword}%')"

            for field in fields

        ]

        conditions.append(

            "("

            + " OR ".join(
                field_conditions
            )

            + ")"

        )

    return " OR ".join(
        conditions
    )
