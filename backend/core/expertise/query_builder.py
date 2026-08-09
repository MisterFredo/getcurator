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
# BUILD UNIVERSE SQL
# ============================================================

def build_universe_sql(
    universe_id: str | None,
) -> str:

    if not universe_id:

        return ""

    return """

    AND EXISTS (

        SELECT 1

        FROM UNNEST(universes) u

        WHERE u.id_universe = @universe_id

    )

    """

# ============================================================
# BUILD SEARCH SQL
# ============================================================

def build_search_sql(
    query: str | None,
) -> str:

    if not query:

        return ""

    return """

    AND (

        LOWER(COALESCE(TITLE,''))

            LIKE LOWER(CONCAT('%', @query, '%'))

        OR

        LOWER(COALESCE(TITLE_EN,''))

            LIKE LOWER(CONCAT('%', @query, '%'))

        OR

        LOWER(COALESCE(EXCERPT,''))

            LIKE LOWER(CONCAT('%', @query, '%'))

        OR

        LOWER(COALESCE(EXCERPT_EN,''))

            LIKE LOWER(CONCAT('%', @query, '%'))

        OR

        LOWER(COALESCE(CONTENT_BODY,''))

            LIKE LOWER(CONCAT('%', @query, '%'))

        OR

        LOWER(COALESCE(SIGNAL_ANALYTIQUE,''))

            LIKE LOWER(CONCAT('%', @query, '%'))

        OR

        LOWER(COALESCE(MECANIQUE_EXPLIQUEE,''))

            LIKE LOWER(CONCAT('%', @query, '%'))

        OR

        LOWER(COALESCE(ENJEU_STRATEGIQUE,''))

            LIKE LOWER(CONCAT('%', @query, '%'))

        OR

        LOWER(COALESCE(POINT_DE_FRICTION,''))

            LIKE LOWER(CONCAT('%', @query, '%'))

    )

    """

# ============================================================
# BUILD SELECTION QUERY
# ============================================================

def build_selection_query(
    profile: ExpertiseProfile,
    period_start: str | None = None,
    period_end: str | None = None,
    limit: int | None = None,
    universe_id: str | None = None,
    query: str | None = None,
) -> tuple[str, dict]:

    selection = build_selection_filters(
        profile,
    )

    query = (
        query.strip()
        if query
        else None
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

    if universe_id:

        params["universe_id"] = (
            universe_id
        )

    if query:

        params["query"] = (
            query
        )

    # ========================================================
    # FILTERS
    # ========================================================

    universe_filter_sql = (
        build_universe_sql(
            universe_id,
        )
    )

    search_filter_sql = (
        build_search_sql(
            query,
        )
    )

    date_filter_sql = ""

    if period_start:

        date_filter_sql += """

        AND PUBLISHED_AT >= @period_start

        """

        params["period_start"] = (
            period_start
        )

    if period_end:

        date_filter_sql += """

        AND PUBLISHED_AT < @period_end

        """

        params["period_end"] = (
            period_end
        )

    # ========================================================
    # LIMIT
    # ========================================================

    limit_sql = ""

    if limit:

        limit_sql = f"""

        LIMIT {limit}

        """

    # ========================================================
    # LANGUAGE
    # ========================================================

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

    # ========================================================
    # QUERY
    # ========================================================

    sql = f"""

    SELECT

        ID_CONTENT AS id,

        {title_sql},

        {excerpt_sql},

        PUBLISHED_AT AS published_at,

        SOURCE_ID AS source_id,

        SOURCE_TITLE AS source_title,

        SOURCE_URL AS source_url,

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

        {universe_filter_sql}

        {search_filter_sql}

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
