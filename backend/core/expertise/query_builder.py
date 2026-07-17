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

    params: dict = {}

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

    sql = f"""

    SELECT
        id_content AS id,
        {title_sql},
        {excerpt_sql},

        published_at,
        source_url,
        source_title,
        source_id,
        ID_PRIMARY_COMPANY,
        content_body,
        signal_analytique,
        mecanique_expliquee,
        enjeu_strategique,
        point_de_friction,
        chiffres,
        companies,
        solutions,
        topics,
        universes,
        concepts

    FROM `{TABLE_CONTENT_ENRICHED}`

    WHERE

        is_active = TRUE

        AND status = "PUBLISHED"

        {date_filter_sql}

        AND (

            ({selection.filters_sql})

            OR

            ({selection.keywords_sql})

        )

    ORDER BY

        published_at DESC

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

        company_ids=(
            profile.preferences.companies
        ),

        solution_ids=(
            profile.preferences.solutions
        ),

        topic_ids=(
            profile.preferences.topics
        ),

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

        ids = ",".join(
            f"'{x}'"
            for x in company_ids
        )

        filters.append(
            f"""
            EXISTS (
                SELECT 1
                FROM UNNEST(companies) c
                WHERE c.id_company IN ({ids})
            )
            """
        )

    if solution_ids:

        ids = ",".join(
            f"'{x}'"
            for x in solution_ids
        )

        filters.append(
            f"""
            EXISTS (
                SELECT 1
                FROM UNNEST(solutions) s
                WHERE s.id_solution IN ({ids})
            )
            """
        )

    if topic_ids:

        ids = ",".join(
            f"'{x}'"
            for x in topic_ids
        )

        filters.append(
            f"""
            EXISTS (
                SELECT 1
                FROM UNNEST(topics) t
                WHERE t.id_topic IN ({ids})
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
