from typing import Dict, Tuple, List

from utils.bigquery_utils import (
    query_bq,
)

from .content_mapper import (
    normalize_contents,
)


# ============================================================
# SELECT CONTENTS
# ============================================================

def select_contents(
    profile: Dict,
    period_start: str | None = None,
    period_end: str | None = None,
    limit: int | None = None,
) -> List[Dict]:

    sql, params = build_selection_query(
        profile=profile,
        period_start=period_start,
        period_end=period_end,
        limit=limit,
    )

    rows = query_bq(
        sql=sql,
        params=params,
    )

    return normalize_contents(
        rows
    )

# ============================================================
# BUILD SELECTION QUERY
# ============================================================

def build_selection_query(
    profile: Dict,
    period_start: str | None = None,
    period_end: str | None = None,
    limit: int | None = None,
) -> Tuple[str, Dict]:

    language = (
        profile.get("language")
        or "fr"
    ).lower()

    is_en = (
        language == "en"
    )

    selection = build_selection_filters(
        profile
    )

    filters_sql = (
        selection["filters_sql"]
    )

    keywords_sql = (
        selection["keywords_sql"]
    )

    # ========================================================
    # DATE FILTERS
    # ========================================================

    date_filter_sql = ""

    params = {}

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

        concepts

    FROM `{TABLE_CONTENT_ENRICHED}`

    WHERE

        is_active = TRUE

        AND status = "PUBLISHED"

        {date_filter_sql}

        AND (

            ({filters_sql})

            OR

            ({keywords_sql})

        )

    ORDER BY

        published_at DESC

    {limit_sql}

    """

    return (
        sql,
        params,
    )


# ============================================================
# BUILD SELECTION FILTERS
# ============================================================

def build_selection_filters(
    profile: Dict,
) -> Dict[str, str]:

    preferences = (
        profile.get("preferences")
        or {}
    )

    company_ids = (
        preferences.get("companies")
        or []
    )

    solution_ids = (
        preferences.get("solutions")
        or []
    )

    topic_ids = (
        preferences.get("topics")
        or []
    )

    keywords = (
        profile.get("keywords")
        or []
    )

    filters_sql = build_filters(
        company_ids=company_ids,
        solution_ids=solution_ids,
        topic_ids=topic_ids,
    )

    keywords_sql = build_keywords_filter(
        keywords
    )

    if not keywords_sql:
        keywords_sql = "FALSE"

    return {

        "filters_sql":
            filters_sql,

        "keywords_sql":
            keywords_sql,
    }
    
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
