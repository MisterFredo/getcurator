from typing import List, Dict, Optional

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq

from core.user.user_service import get_user_context


# ============================================================
# TABLES / VIEWS
# ============================================================

TABLE_CONTENT_ENRICHED = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_ENRICHED"
)

VIEW_STATS_SOLUTION = (
    f"{BQ_PROJECT}.{BQ_DATASET}.V_CONTENT_STATS_SOLUTION"
)

TABLE_SOLUTION = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION"
)

TABLE_COMPANY = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY"
)

TABLE_COMPANY_UNIVERSE = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY_UNIVERSE"
)

TABLE_USER_UNIVERSE = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_UNIVERSE"
)


# ============================================================
# FEED
# ============================================================

def _get_solution_feed(
    solution_id: str,
    limit: int = 50,
    offset: int = 0,
    user_id: Optional[str] = None,
    universe_id: Optional[str] = None,
    lang: str = "fr",
) -> List[Dict]:

    user_filter = ""

    if user_id:

        user_filter = f"""
        AND EXISTS (
            SELECT 1
            FROM UNNEST(c.companies) comp

            JOIN `{TABLE_COMPANY_UNIVERSE}` cu
              ON cu.ID_COMPANY = comp.id_company

            JOIN `{TABLE_USER_UNIVERSE}` uu
              ON uu.ID_UNIVERSE = cu.ID_UNIVERSE

            WHERE uu.ID_USER = @user_id
        )
        """

    universe_filter = ""

    if universe_id:

        universe_filter = f"""
        AND EXISTS (
            SELECT 1
            FROM UNNEST(c.companies) comp

            JOIN `{TABLE_COMPANY_UNIVERSE}` cu
              ON cu.ID_COMPANY = comp.id_company

            WHERE cu.ID_UNIVERSE = @universe_id
        )
        """

    sql = f"""
    SELECT

        c.id_content AS id,

        c.title,
        c.title_en,

        c.excerpt,
        c.excerpt_en,

        c.published_at

    FROM `{TABLE_CONTENT_ENRICHED}` c

    WHERE EXISTS (

        SELECT 1

        FROM UNNEST(c.solutions) s

        WHERE s.id_solution = @solution_id

    )

    {user_filter}

    {universe_filter}

    ORDER BY c.published_at DESC

    LIMIT @limit
    OFFSET @offset
    """

    rows = query_bq(
        sql,
        {
            "solution_id": solution_id,
            "limit": limit,
            "offset": offset,
            "user_id": user_id,
            "universe_id": universe_id,
        },
    )

    return [
        _map_content(
            row,
            lang,
        )
        for row in rows
    ]


# ============================================================
# PUBLIC VIEW
# ============================================================

def get_solution_view(
    solution_id: str,
    limit: int = 50,
    offset: int = 0,
    user_id: Optional[str] = None,
    universe_id: Optional[str] = None,
) -> Optional[Dict]:

    solution_rows = query_bq(
        f"""
        SELECT

            s.ID_SOLUTION,
            s.NAME,

            c.NAME AS COMPANY_NAME,
            c.MEDIA_LOGO_RECTANGLE_ID

        FROM `{TABLE_SOLUTION}` s

        LEFT JOIN `{TABLE_COMPANY}` c
            ON c.ID_COMPANY = s.ID_COMPANY

        WHERE s.ID_SOLUTION = @solution_id

        LIMIT 1
        """,
        {
            "solution_id": solution_id,
        },
    )

    if not solution_rows:
        return None

    solution = solution_rows[0]

    stats_rows = query_bq(
        f"""
        SELECT

            COALESCE(total, 0) AS NB_ANALYSES,

            COALESCE(last_30_days, 0) AS DELTA_30D

        FROM `{VIEW_STATS_SOLUTION}`

        WHERE id_solution = @solution_id

        LIMIT 1
        """,
        {
            "solution_id": solution_id,
        },
    )

    stats = stats_rows[0] if stats_rows else {}

    context = (
        get_user_context(user_id)
        if user_id
        else None
    )

    lang = (
        context["lang"]
        if context
        else "fr"
    )

    items = _get_solution_feed(
        solution_id=solution_id,
        limit=limit,
        offset=offset,
        user_id=user_id,
        universe_id=universe_id,
        lang=lang,
    )

    return {

        "id_solution": solution_id,

        "name": solution.get("NAME"),

        "company_name": solution.get("COMPANY_NAME"),

        "media_logo_rectangle_id": solution.get(
            "MEDIA_LOGO_RECTANGLE_ID"
        ),

        "nb_analyses": stats.get(
            "NB_ANALYSES",
            0,
        ),

        "delta_30d": stats.get(
            "DELTA_30D",
            0,
        ),

        "items": items,
    }


def list_solutions_for_user(
    user_id: str,
) -> List[Dict]:

    rows = query_bq(
        f"""
        SELECT
            s.ID_SOLUTION,
            s.NAME,
            s.ID_COMPANY,

            s.MEDIA_LOGO_RECTANGLE_ID
                AS SOLUTION_LOGO,

            c.NAME
                AS COMPANY_NAME,

            c.MEDIA_LOGO_RECTANGLE_ID,

            CAST(
                c.IS_PARTNER AS BOOL
            ) AS IS_PARTNER,

            s.CREATED_AT,
            s.UPDATED_AT,

            ns.ID_SOLUTION IS NOT NULL
                AS HAS_NUMBERS,

            ARRAY_AGG(
                DISTINCT u.LABEL
                IGNORE NULLS
            ) AS UNIVERSES

        FROM `{TABLE_SOLUTION}` s

        JOIN `{TABLE_COMPANY}` c
            ON c.ID_COMPANY = s.ID_COMPANY

        JOIN `{TABLE_COMPANY_UNIVERSE}` cu
            ON cu.ID_COMPANY = c.ID_COMPANY

        JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_UNIVERSE` u
            ON u.ID_UNIVERSE = cu.ID_UNIVERSE

        JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_UNIVERSE` uu
            ON uu.ID_UNIVERSE = cu.ID_UNIVERSE

        LEFT JOIN (
            SELECT DISTINCT ID_SOLUTION
            FROM `{TABLE_NUMBERS_SOLUTION}`
        ) ns
            ON ns.ID_SOLUTION = s.ID_SOLUTION

        WHERE
            s.IS_ACTIVE = TRUE
            AND uu.ID_USER = @user_id

        GROUP BY
            s.ID_SOLUTION,
            s.NAME,
            s.ID_COMPANY,
            s.MEDIA_LOGO_RECTANGLE_ID,
            c.NAME,
            c.MEDIA_LOGO_RECTANGLE_ID,
            c.IS_PARTNER,
            s.CREATED_AT,
            s.UPDATED_AT,
            ns.ID_SOLUTION

        ORDER BY
            UPPER(s.NAME)
        """,
        {
            "user_id": user_id,
        },
    )

    return [
        {
            "id_solution": r["ID_SOLUTION"],

            "name": r["NAME"],

            "id_company": r["ID_COMPANY"],

            "company_name": r.get(
                "COMPANY_NAME"
            ),

            "media_logo_rectangle_id": (
                r.get("SOLUTION_LOGO")
                or r.get(
                    "MEDIA_LOGO_RECTANGLE_ID"
                )
            ),

            "logo_type": (
                "solution"
                if r.get("SOLUTION_LOGO")
                else "company"
            ),

            "is_partner": r.get(
                "IS_PARTNER",
                False,
            ),

            "created_at": r.get(
                "CREATED_AT",
            ),

            "updated_at": r.get(
                "UPDATED_AT",
            ),

            "has_numbers": r.get(
                "HAS_NUMBERS",
                False,
            ),

            "universes": (
                r.get("UNIVERSES")
                or []
            ),
        }
        for r in rows
    ]

# ============================================================
# CONTENT MAPPER
# ============================================================

def _map_content(
    row: Dict,
    lang: str = "fr",
) -> Dict:

    def fmt(value):
        return value.isoformat() if value else None

    return {

        "id": row.get("id"),

        "title": (
            row.get("title_en")
            if lang == "en"
            else None
        ) or row.get("title"),

        "title_en": row.get("title_en"),

        "excerpt": (
            row.get("excerpt_en")
            if lang == "en"
            else None
        ) or row.get("excerpt"),

        "excerpt_en": row.get("excerpt_en"),

        "published_at": fmt(
            row.get("published_at")
        ),
    }
