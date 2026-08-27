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
# BUILD ALLOWED UNIVERSES SQL
# ============================================================

def build_allowed_universes_sql(
    allowed_universe_ids: list[str] | None,
) -> str:

    # None signifie que l'appelant ne demande pas
    # de restriction par droits utilisateur.
    if allowed_universe_ids is None:

        return ""

    # Une liste vide signifie que le user
    # n'a accès à aucun univers.
    if not allowed_universe_ids:

        return """

        AND FALSE

        """

    return """

    AND EXISTS (

        SELECT 1

        FROM UNNEST(universes) u

        WHERE u.id_universe
            IN UNNEST(@allowed_universe_ids)

    )

    """


# ============================================================
# BUILD ENTITY SQL
# ============================================================

def build_entity_sql(
    company_id: str | None = None,
    solution_id: str | None = None,
    topic_id: str | None = None,
) -> str:

    filters = []

    if company_id:

        filters.append(
            """
            EXISTS (
                SELECT 1
                FROM UNNEST(companies) c
                WHERE c.id_company = @company_id
            )
            """
        )

    if solution_id:

        filters.append(
            """
            EXISTS (
                SELECT 1
                FROM UNNEST(solutions) s
                WHERE s.id_solution = @solution_id
            )
            """
        )

    if topic_id:

        filters.append(
            """
            EXISTS (
                SELECT 1
                FROM UNNEST(topics) t
                WHERE t.id_topic = @topic_id
            )
            """
        )

    if not filters:

        return ""

    return " AND ".join(filters)


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
# BUILD SELECTION CONTEXT
# ============================================================

# ============================================================
# BUILD SELECTION CONTEXT
# ============================================================

def build_selection_context(
    profile: ExpertiseProfile,
    period_start: str | None = None,
    period_end: str | None = None,
    universe_id: str | None = None,
    query: str | None = None,
    company_id: str | None = None,
    solution_id: str | None = None,
    topic_id: str | None = None,
    apply_profile_selection: bool = True,
    allowed_universe_ids: list[str] | None = None,
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

        "company_ids":
            profile.preferences.companies,

        "solution_ids":
            profile.preferences.solutions,

        "topic_ids":
            profile.preferences.topics,

    }

    # ========================================================
    # ALLOWED UNIVERSES
    # ========================================================

    if allowed_universe_ids:

        params["allowed_universe_ids"] = (
            allowed_universe_ids
        )

    # ========================================================
    # EXPLICIT FILTERS
    # ========================================================

    if universe_id:

        params["universe_id"] = (
            universe_id
        )

    if query:

        params["query"] = (
            query
        )

    if company_id:

        params["company_id"] = (
            company_id
        )

    if solution_id:

        params["solution_id"] = (
            solution_id
        )

    if topic_id:

        params["topic_id"] = (
            topic_id
        )

    # ========================================================
    # FILTER SQL
    # ========================================================

    allowed_universes_filter_sql = (
        build_allowed_universes_sql(
            allowed_universe_ids,
        )
    )

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

    entity_filter_sql = (
        build_entity_sql(
            company_id=company_id,
            solution_id=solution_id,
            topic_id=topic_id,
        )
    )

    # ========================================================
    # DATE
    # ========================================================

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
    # SELECTION
    # ========================================================

    if entity_filter_sql:

        selection_sql = f"""
        AND (
            {entity_filter_sql}
        )
        """

    elif apply_profile_selection:

        selection_sql = f"""
        AND (
            ({selection.filters_sql})
            OR
            ({selection.keywords_sql})
        )
        """

    else:

        selection_sql = ""

    # ========================================================
    # FINAL FILTERS
    # ========================================================

    filters_sql = f"""

        {allowed_universes_filter_sql}

        {universe_filter_sql}

        {search_filter_sql}

        {date_filter_sql}

        {selection_sql}

    """

    return (
        filters_sql,
        params,
    )

# ============================================================
# BUILD SELECTION QUERY
# ============================================================

def build_selection_query(
    profile: ExpertiseProfile,
    period_start: str | None = None,
    period_end: str | None = None,
    limit: int | None = None,
    offset: int = 0,
    universe_id: str | None = None,
    query: str | None = None,
    company_id: str | None = None,
    solution_id: str | None = None,
    topic_id: str | None = None,
    apply_profile_selection: bool = True,
    allowed_universe_ids: list[str] | None = None,
) -> tuple[str, dict]:

    # ========================================================
    # COMMON FILTERS
    # ========================================================

    filters_sql, params = (
        build_selection_context(

            profile=profile,

            period_start=period_start,

            period_end=period_end,

            universe_id=universe_id,

            query=query,

            company_id=company_id,

            solution_id=solution_id,

            topic_id=topic_id,

            apply_profile_selection=apply_profile_selection,

            allowed_universe_ids=allowed_universe_ids,

        )
    )

    # ========================================================
    # PAGINATION
    # ========================================================

    pagination_sql = ""

    if limit is not None:

        pagination_sql = """

        LIMIT @limit

        OFFSET @offset

        """

        params["limit"] = (
            limit
        )

        params["offset"] = (
            offset
        )

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

        {filters_sql}

    ORDER BY

        PUBLISHED_AT DESC

    {pagination_sql}

    """

    return (
        sql,
        params,
    )

# ============================================================
# BUILD SELECTION COUNT QUERY
# ============================================================

def build_selection_count_query(
    profile: ExpertiseProfile,
    period_start: str | None = None,
    period_end: str | None = None,
    universe_id: str | None = None,
    query: str | None = None,
    company_id: str | None = None,
    solution_id: str | None = None,
    topic_id: str | None = None,
    apply_profile_selection: bool = True,
    allowed_universe_ids: list[str] | None = None,
) -> tuple[str, dict]:

    filters_sql, params = (
        build_selection_context(

            profile=profile,

            period_start=period_start,

            period_end=period_end,

            universe_id=universe_id,

            query=query,

            company_id=company_id,

            solution_id=solution_id,

            topic_id=topic_id,

            apply_profile_selection=apply_profile_selection,

            allowed_universe_ids=allowed_universe_ids,

        )
    )

    sql = f"""

    SELECT

        COUNT(*) AS total

    FROM `{TABLE_CONTENT_ENRICHED}`

    WHERE

        IS_ACTIVE = TRUE

        AND STATUS = "PUBLISHED"

        {filters_sql}

    """

    return (
        sql,
        params,
    )
# ============================================================
# BUILD SELECTION FILTERS
# ============================================================

def build_selection_filters(
    profile: ExpertiseProfile,
) -> SelectionFilters:

    filters_sql = build_filters_sql(

        company_ids=
            profile.preferences.companies,

        solution_ids=
            profile.preferences.solutions,

        topic_ids=
            profile.preferences.topics,

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

        "TITLE",

        "TITLE_EN",

        "EXCERPT",

        "EXCERPT_EN",

        "CONTENT_BODY",

        "SIGNAL_ANALYTIQUE",

        "MECANIQUE_EXPLIQUEE",

        "ENJEU_STRATEGIQUE",

        "POINT_DE_FRICTION",

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
