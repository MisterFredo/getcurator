from core.expertise.profile_service import (
    load_profile,
)

from core.expertise.query_builder import (
    build_selection_context,
)

from utils.bigquery_utils import (
    query_bq,
)

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)


TABLE_CONTENT_ENRICHED = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_CONTENT_ENRICHED"
)


# ============================================================
# GET WATCH FILTERS
# ============================================================

def get_watch_filters(
    user_id: str,
    period_start: str | None = None,
    period_end: str | None = None,
):

    # ========================================================
    # PROFILE
    # ========================================================

    profile = load_profile(
        user_id=user_id,
    )

    # ========================================================
    # BASE PROFILE SELECTION
    # ========================================================

    filters_sql, params = (
        build_selection_context(

            profile=profile,

            period_start=period_start,

            period_end=period_end,

        )
    )

    # ========================================================
    # FACETS
    # ========================================================

    sql = f"""

    WITH base AS (

        SELECT

            ID_CONTENT,

            COMPANIES AS companies,

            SOLUTIONS AS solutions,

            TOPICS AS topics,

            UNIVERSES AS universes

        FROM `{TABLE_CONTENT_ENRICHED}`

        WHERE

            IS_ACTIVE = TRUE

            AND STATUS = "PUBLISHED"

            {filters_sql}

    ),

    facets AS (

        SELECT

            "company" AS filter_type,

            c.id_company AS id,

            c.name AS label,

            COUNT(
                DISTINCT ID_CONTENT
            ) AS count

        FROM base

        CROSS JOIN UNNEST(
            companies
        ) c

        WHERE

            c.id_company IS NOT NULL

            AND c.name IS NOT NULL

        GROUP BY

            c.id_company,

            c.name


        UNION ALL


        SELECT

            "solution" AS filter_type,

            s.id_solution AS id,

            s.name AS label,

            COUNT(
                DISTINCT ID_CONTENT
            ) AS count

        FROM base

        CROSS JOIN UNNEST(
            solutions
        ) s

        WHERE

            s.id_solution IS NOT NULL

            AND s.name IS NOT NULL

        GROUP BY

            s.id_solution,

            s.name


        UNION ALL


        SELECT

            "topic" AS filter_type,

            t.id_topic AS id,

            t.label AS label,

            COUNT(
                DISTINCT ID_CONTENT
            ) AS count

        FROM base

        CROSS JOIN UNNEST(
            topics
        ) t

        WHERE

            t.id_topic IS NOT NULL

            AND t.label IS NOT NULL

        GROUP BY

            t.id_topic,

            t.label


        UNION ALL


        SELECT

            "universe" AS filter_type,

            u.id_universe AS id,

            u.label AS label,

            COUNT(
                DISTINCT ID_CONTENT
            ) AS count

        FROM base

        CROSS JOIN UNNEST(
            universes
        ) u

        WHERE

            u.id_universe IS NOT NULL

            AND u.label IS NOT NULL

        GROUP BY

            u.id_universe,

            u.label

    )

    SELECT

        filter_type,

        id,

        label,

        count

    FROM facets

    ORDER BY

        filter_type,

        count DESC,

        label

    """

    rows = query_bq(

        sql=sql,

        params=params,

    )

    # ========================================================
    # RESPONSE
    # ========================================================

    result = {

        "universes": [],

        "companies": [],

        "solutions": [],

        "topics": [],

    }

    key_by_type = {

        "universe":
            "universes",

        "company":
            "companies",

        "solution":
            "solutions",

        "topic":
            "topics",

    }

    for row in rows:

        key = key_by_type.get(
            row.get(
                "filter_type"
            )
        )

        if not key:

            continue

        result[key].append({

            "id":
                row.get(
                    "id"
                ),

            "label":
                row.get(
                    "label"
                ),

            "count":
                int(
                    row.get(
                        "count"
                    )
                    or 0
                ),

        })

    return result
