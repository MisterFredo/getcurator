from typing import List, Dict, Optional

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq


TABLE_CONTENT_ENRICHED = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_ENRICHED"
)


# ============================================================
# 🔥 USER FILTER FACTO (SOURCE_ID cohérent)
# ============================================================

def build_user_filter(alias: str = "c") -> str:
    return f"""
    AND EXISTS (
        SELECT 1
        FROM UNNEST({alias}.universes) u
        JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_UNIVERSE` uu
          ON uu.ID_UNIVERSE = u.id_universe
        WHERE uu.ID_USER = @user_id
    )
    """


# ============================================================
# SEARCH
# ============================================================

def search(
    q: str,
    limit: int = 20,
    offset: int = 0,
    user_id: Optional[str] = None,
    universe_id: Optional[str] = None,
) -> List[Dict]:

    q = (q or "").strip()

    universe_filter = ""

    if universe_id:
        universe_filter = """
        AND EXISTS (
            SELECT 1
            FROM UNNEST(c.universes) u
            WHERE u.id_universe = @universe_id
        )
        """

    sql = f"""
    SELECT

        c.id_content AS id,

        LOWER(
            COALESCE(c.content_type, 'ANALYSIS')
        ) AS type,

        -- 🔥 NEW
        c.primary_company_id,

        -- 🔥 NEW
        c.primary_company_name,

        c.title,
        c.excerpt,
        c.published_at,

        c.topics,
        c.universes,
        c.companies,
        c.solutions,
        c.concepts,
        c.source_id,

        (
            CASE
                WHEN LOWER(c.title)
                    LIKE LOWER(CONCAT('%', @query, '%'))
                THEN 3

                WHEN LOWER(c.excerpt)
                    LIKE LOWER(CONCAT('%', @query, '%'))
                THEN 2

                ELSE 0
            END

            +

            CASE
                WHEN EXISTS (
                    SELECT 1
                    FROM UNNEST(c.companies) co
                    WHERE LOWER(co.name)
                        LIKE LOWER(CONCAT('%', @query, '%'))
                )
                THEN 2

                ELSE 0
            END

            +

            CASE
                WHEN EXISTS (
                    SELECT 1
                    FROM UNNEST(c.solutions) s
                    WHERE LOWER(s.name)
                        LIKE LOWER(CONCAT('%', @query, '%'))
                )
                THEN 2

                ELSE 0
            END
        ) AS score

    FROM `{TABLE_CONTENT_ENRICHED}` c

    WHERE
    (
        LOWER(c.title)
            LIKE LOWER(CONCAT('%', @query, '%'))

        OR LOWER(c.excerpt)
            LIKE LOWER(CONCAT('%', @query, '%'))

        OR EXISTS (
            SELECT 1
            FROM UNNEST(c.companies) co
            WHERE LOWER(co.name)
                LIKE LOWER(CONCAT('%', @query, '%'))
        )

        OR EXISTS (
            SELECT 1
            FROM UNNEST(c.solutions) s
            WHERE LOWER(s.name)
                LIKE LOWER(CONCAT('%', @query, '%'))
        )
    )

    {build_user_filter("c")}

    {universe_filter}

    ORDER BY
        score DESC,
        published_at DESC

    LIMIT @limit
    OFFSET @offset
    """

    params = {
        "query": q,
        "limit": limit,
        "offset": offset,
        "user_id": user_id,
        "universe_id": universe_id,
    }

    rows = query_bq(sql, params)

    return [_map_feed_row(r) for r in rows]


# ============================================================
# LATEST
# ============================================================

def latest(
    limit: int = 20,
    offset: int = 0,
    user_id: Optional[str] = None,
    universe_id: Optional[str] = None,
) -> List[Dict]:

    universe_filter = ""

    if universe_id:
        universe_filter = """
        AND EXISTS (
            SELECT 1
            FROM UNNEST(c.universes) u
            WHERE u.id_universe = @universe_id
        )
        """

    sql = f"""
    SELECT

        c.id_content AS id,

        LOWER(
            COALESCE(c.content_type, 'ANALYSIS')
        ) AS type,

        -- 🔥 NEW
        c.primary_company_id,

        -- 🔥 NEW
        c.primary_company_name,

        c.title,
        c.excerpt,
        c.published_at,

        c.topics,
        c.universes,
        c.companies,
        c.solutions,
        c.concepts,
        c.source_id

    FROM `{TABLE_CONTENT_ENRICHED}` c

    WHERE c.published_at IS NOT NULL

    {build_user_filter("c")}

    {universe_filter}

    ORDER BY published_at DESC

    LIMIT @limit
    OFFSET @offset
    """

    params = {
        "limit": limit,
        "offset": offset,
        "universe_id": universe_id,
        "user_id": user_id,
    }

    rows = query_bq(sql, params)

    return [_map_feed_row(r) for r in rows]


# ============================================================
# ITEM
# ============================================================

def get_item_curator(
    item_id: str,
    user_id: Optional[str] = None
) -> Optional[Dict]:

    sql = f"""
    SELECT

        c.id_content AS id,

        LOWER(
            COALESCE(c.content_type, 'ANALYSIS')
        ) AS type,

        -- 🔥 NEW
        c.primary_company_id,

        -- 🔥 NEW
        c.primary_company_name,

        c.title,
        c.excerpt,
        c.published_at,

        c.topics,
        c.companies,
        c.solutions,
        c.concepts,

        SAFE_CAST(c.source_id AS STRING) AS id_source

    FROM `{TABLE_CONTENT_ENRICHED}` c

    WHERE c.id_content = @id

    AND (
        @user_id IS NULL

        OR EXISTS (
            SELECT 1

            FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOURCE_UNIVERSE` su

            JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_UNIVERSE` uu
              ON uu.ID_UNIVERSE = su.ID_UNIVERSE

            WHERE uu.ID_USER = @user_id
              AND su.ID_SOURCE = c.source_id
        )
    )

    LIMIT 1
    """

    rows = query_bq(sql, {
        "id": item_id,
        "user_id": user_id,
    })

    if not rows:
        return None

    return _map_feed_row(rows[0])


# ============================================================
# DETAIL
# ============================================================

def get_item_detail(
    item_id: str,
    user_id: Optional[str] = None
) -> Optional[Dict]:

    item = get_item_curator(
        item_id,
        user_id=user_id
    )

    if not item:
        return None

    from core.content.public_service import get_content

    content = get_content(item_id)

    if not content:
        return None

    return {
        **content,
        "topics": item.get("topics", []),
        "companies": item.get("companies", []),
        "solutions": item.get("solutions", []),
    }


# ============================================================
# STATS
# ============================================================

def get_content_stats():

    global_rows = query_bq(f"""
        SELECT *
        FROM `{BQ_PROJECT}.{BQ_DATASET}.V_CONTENT_STATS_GLOBAL`
    """)

    if global_rows:

        g = global_rows[0]

        total_count = g.get("total", 0) or 0
        last_7 = g.get("last_7_days", 0) or 0
        last_30 = g.get("last_30_days", 0) or 0

    else:

        total_count = 0
        last_7 = 0
        last_30 = 0

    topics_rows = query_bq(f"""
        SELECT *
        FROM `{BQ_PROJECT}.{BQ_DATASET}.V_CONTENT_STATS_TOPIC`
        ORDER BY total DESC
    """)

    topics_stats = [
        {
            "id_topic": r.get("id_topic"),
            "label": r.get("label"),
            "total_count": r.get("total", 0) or 0,
            "last_7_days": r.get("last_7_days", 0) or 0,
            "last_30_days": r.get("last_30_days", 0) or 0,
        }
        for r in topics_rows
        if r.get("id_topic") and r.get("label")
    ]

    company_rows = query_bq(f"""
        SELECT *
        FROM `{BQ_PROJECT}.{BQ_DATASET}.V_CONTENT_STATS_COMPANY`
        ORDER BY total DESC
    """)

    top_companies = [
        {
            "id_company": r.get("id_company"),
            "name": r.get("name"),
            "total_count": r.get("total", 0) or 0,
            "last_7_days": r.get("last_7_days", 0) or 0,
            "last_30_days": r.get("last_30_days", 0) or 0,
        }
        for r in company_rows
        if r.get("id_company") and r.get("name")
    ]

    solution_rows = query_bq(f"""
        SELECT *
        FROM `{BQ_PROJECT}.{BQ_DATASET}.V_CONTENT_STATS_SOLUTION`
        ORDER BY total DESC
    """)

    top_solutions = [
        {
            "id_solution": r.get("id_solution"),
            "name": r.get("name"),
            "total_count": r.get("total", 0) or 0,
            "last_7_days": r.get("last_7_days", 0) or 0,
            "last_30_days": r.get("last_30_days", 0) or 0,
        }
        for r in solution_rows
        if r.get("id_solution") and r.get("name")
    ]

    return {
        "total_count": total_count,
        "last_7_days": last_7,
        "last_30_days": last_30,
        "topics_stats": topics_stats,
        "top_companies": top_companies,
        "top_solutions": top_solutions,
    }


# ============================================================
# MAPPER
# ============================================================

def _map_feed_row(r: Dict) -> Dict:

    topics = r.get("topics") or []
    companies = r.get("companies") or []
    solutions = r.get("solutions") or []
    concepts = r.get("concepts") or []
    universes = r.get("universes") or []

    badges = []

    # =====================================================
    # TOPICS
    # =====================================================

    for t in topics:

        if isinstance(t, dict):

            badges.append({
                "type": "topic",
                "label": t.get("label") or t.get("name"),
                "id": t.get("id_topic"),
            })

        else:

            badges.append({
                "type": "topic",
                "label": t,
            })

    # =====================================================
    # CONCEPTS
    # =====================================================

    for c in concepts:

        if isinstance(c, dict):

            badges.append({
                "type": "concept",
                "label": c.get("label"),
                "id": c.get("id_concept"),
            })

        else:

            badges.append({
                "type": "concept",
                "label": c,
            })

    # =====================================================
    # COMPANIES
    # =====================================================

    for c in companies:

        badges.append({
            "type": "company",
            "label": c.get("name"),
            "id": c.get("id_company"),
        })

    # =====================================================
    # SOLUTIONS
    # =====================================================

    for s in solutions:

        badges.append({
            "type": "solution",
            "label": s.get("name"),
            "id": s.get("id_solution"),
        })

    # =====================================================
    # UNIVERS
    # =====================================================

    for u in universes:

        badges.append({
            "type": "universe",
            "label": u.get("label"),
            "id": u.get("id_universe"),
        })

    return {
        "id": r.get("id"),

        "type": r.get("type"),

        # 🔥 NEW
        "primary_company_id": r.get(
            "primary_company_id"
        ),

        # 🔥 NEW
        "primary_company_name": r.get(
            "primary_company_name"
        ),

        "title": r.get("title"),

        "excerpt": r.get("excerpt"),

        "published_at": r.get("published_at"),

        "topics": topics,

        "companies": companies,

        "solutions": solutions,

        "concepts": concepts,

        "universes": universes,

        "badges": badges,
    }
