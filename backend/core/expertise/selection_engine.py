from typing import Dict


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
