from typing import List, Dict, Optional

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq

from core.company.service import get_company


# ============================================================
# TABLES / VIEWS
# ============================================================

VIEW_CONTENT = f"{BQ_PROJECT}.{BQ_DATASET}.V_CONTENT_ENRICHED"

VIEW_STATS_COMPANY = f"{BQ_PROJECT}.{BQ_DATASET}.V_CONTENT_STATS_COMPANY"
VIEW_STATS_TOPIC = f"{BQ_PROJECT}.{BQ_DATASET}.V_CONTENT_STATS_TOPIC"
VIEW_STATS_SOLUTION = f"{BQ_PROJECT}.{BQ_DATASET}.V_CONTENT_STATS_SOLUTION"

TABLE_TOPIC = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOPIC"
TABLE_SOLUTION = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION"
TABLE_COMPANY_UNIVERSE = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY_UNIVERSE"
TABLE_USER_UNIVERSE = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_UNIVERSE"


# ============================================================
# 🔥 GENERIC FEED BUILDER (CONTENT ONLY)
# ============================================================

def _get_entity_feed(
    where_clause_content: str,
    params: Dict,
    limit: int = 50,
    offset: int = 0,
    user_id: Optional[str] = None,
    universe_id: Optional[str] = None,
) -> List[Dict]:

    # ============================================================
    # 🔐 USER FILTER
    # ============================================================

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

    # ============================================================
    # 🌍 UNIVERSE FILTER
    # ============================================================

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

    # ============================================================
    # QUERY
    # ============================================================

    sql = f"""
    SELECT
        c.id_content AS id,
        'analysis' AS type,
        c.title,
        c.excerpt,
        c.published_at,
        NULL AS news_type,
        c.topics,
        c.companies,
        c.solutions

    FROM `{VIEW_CONTENT}` c

    WHERE {where_clause_content}
    {user_filter}
    {universe_filter}

    ORDER BY c.published_at DESC
    LIMIT @limit
    OFFSET @offset
    """

    query_params = {
        **params,
        "limit": limit,
        "offset": offset,
        "user_id": user_id,
    }

    if universe_id:
        query_params["universe_id"] = universe_id

    rows = query_bq(sql, query_params)

    return [_map_feed_row(r) for r in rows]


# ============================================================
# COMPANY
# ============================================================

def get_company_feed(
    company_id: str,
    limit: int = 50,
    offset: int = 0,
    user_id: Optional[str] = None,
    universe_id: Optional[str] = None
) -> List[Dict]:

    # ============================================================
    # 🔐 USER FILTER
    # ============================================================

    user_filter = ""

    if user_id:
        user_filter = f"""
        AND EXISTS (
            SELECT 1
            FROM `{TABLE_COMPANY_UNIVERSE}` cu
            JOIN `{TABLE_USER_UNIVERSE}` uu
              ON uu.ID_UNIVERSE = cu.ID_UNIVERSE
            WHERE cu.ID_COMPANY = cc.ID_COMPANY
              AND uu.ID_USER = @user_id
        )
        """

    # ============================================================
    # 🌍 UNIVERSE FILTER
    # ============================================================

    universe_filter = ""

    if universe_id:
        universe_filter = f"""
        AND EXISTS (
            SELECT 1
            FROM `{TABLE_COMPANY_UNIVERSE}` cu
            WHERE cu.ID_COMPANY = cc.ID_COMPANY
              AND cu.ID_UNIVERSE = @universe_id
        )
        """

    # ============================================================
    # 1️⃣ FILTER FIRST (FAST)
    # ============================================================

    sql_ids = f"""
    SELECT
        c.ID_CONTENT
    FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT` c
    JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_COMPANY` cc
        ON cc.ID_CONTENT = c.ID_CONTENT

    WHERE
        cc.ID_COMPANY = @company_id
        AND c.STATUS = 'PUBLISHED'
        AND c.IS_ACTIVE = TRUE
        AND c.PUBLISHED_AT IS NOT NULL

        {user_filter}
        {universe_filter}

    ORDER BY c.PUBLISHED_AT DESC

    LIMIT @limit
    OFFSET @offset
    """

    query_params = {
        "company_id": company_id,
        "limit": limit,
        "offset": offset,
        "user_id": user_id,
    }

    if universe_id:
        query_params["universe_id"] = universe_id

    id_rows = query_bq(sql_ids, query_params)

    content_ids = [
        r["ID_CONTENT"]
        for r in id_rows
        if r.get("ID_CONTENT")
    ]

    if not content_ids:
        return []

    # ============================================================
    # 2️⃣ ENRICH ONLY FINAL RESULTS
    # ============================================================

    sql_feed = f"""
    SELECT
        c.id_content AS id,
        'analysis' AS type,
        c.title,
        c.excerpt,
        c.published_at,
        NULL AS news_type,
        c.topics,
        c.companies,
        c.solutions

    FROM `{VIEW_CONTENT}` c

    WHERE c.id_content IN UNNEST(@content_ids)

    ORDER BY c.published_at DESC
    """

    rows = query_bq(sql_feed, {
        "content_ids": content_ids
    })

    return [_map_feed_row(r) for r in rows]


def get_company_view(
    company_id: str,
    limit: int = 50,
    offset: int = 0,
    user_id: Optional[str] = None,
    universe_id: Optional[str] = None
) -> Optional[Dict]:

    company = get_company(company_id)
    if not company:
        return None

    stats_rows = query_bq(f"""
        SELECT
            COALESCE(total, 0) AS NB_ANALYSES,
            COALESCE(last_30_days, 0) AS DELTA_30D
        FROM `{VIEW_STATS_COMPANY}`
        WHERE id_company = @company_id
        LIMIT 1
    """, {"company_id": company_id})

    stats = stats_rows[0] if stats_rows else {}

    items = get_company_feed(company_id, limit, offset, user_id, universe_id)

    return {
        **company,
        "nb_analyses": stats.get("NB_ANALYSES", 0),
        "delta_30d": stats.get("DELTA_30D", 0),
        "items": items
    }


# ============================================================
# TOPIC
# ============================================================

def get_topic_feed(
    topic_id: str,
    limit: int = 50,
    offset: int = 0,
    user_id: Optional[str] = None,
    universe_id: Optional[str] = None
) -> List[Dict]:

    return _get_entity_feed(
        where_clause_content="""
            EXISTS (
                SELECT 1
                FROM UNNEST(c.topics) t
                WHERE t.id_topic = @topic_id
            )
        """,
        params={"topic_id": topic_id},
        limit=limit,
        offset=offset,
        user_id=user_id,
        universe_id=universe_id
    )


def get_topic_view(
    topic_id: str,
    limit: int = 50,
    offset: int = 0,
    user_id: Optional[str] = None,
    universe_id: Optional[str] = None
) -> Dict:

    topic_rows = query_bq(f"""
        SELECT ID_TOPIC, LABEL, TOPIC_AXIS, DESCRIPTION
        FROM `{TABLE_TOPIC}`
        WHERE ID_TOPIC = @topic_id
        LIMIT 1
    """, {"topic_id": topic_id})

    topic = topic_rows[0] if topic_rows else {}

    stats_rows = query_bq(f"""
        SELECT
            COALESCE(total, 0) AS NB_ANALYSES,
            COALESCE(last_30_days, 0) AS DELTA_30D
        FROM `{VIEW_STATS_TOPIC}`
        WHERE id_topic = @topic_id
        LIMIT 1
    """, {"topic_id": topic_id})

    stats = stats_rows[0] if stats_rows else {}

    items = get_topic_feed(topic_id, limit, offset, user_id, universe_id)

    return {
        "id_topic": topic_id,
        "label": topic.get("LABEL"),
        "topic_axis": topic.get("TOPIC_AXIS"),
        "description": topic.get("DESCRIPTION"),
        "nb_analyses": stats.get("NB_ANALYSES", 0),
        "delta_30d": stats.get("DELTA_30D", 0),
        "items": items
    }


# ============================================================
# SOLUTION
# ============================================================

def get_solution_feed(
    solution_id: str,
    limit: int = 50,
    offset: int = 0,
    user_id: Optional[str] = None,
    universe_id: Optional[str] = None
) -> List[Dict]:

    return _get_entity_feed(
        where_clause_content="""
            EXISTS (
                SELECT 1
                FROM UNNEST(c.solutions) s
                WHERE s.id_solution = @solution_id
            )
        """,
        params={"solution_id": solution_id},
        limit=limit,
        offset=offset,
        user_id=user_id,
        universe_id=universe_id
    )


def get_solution_view(
    solution_id: str,
    limit: int = 50,
    offset: int = 0,
    user_id: Optional[str] = None,
    universe_id: Optional[str] = None
) -> Dict:

    solution_rows = query_bq(f"""
        SELECT
            s.ID_SOLUTION,
            s.NAME,
            c.NAME AS COMPANY_NAME,
            c.MEDIA_LOGO_RECTANGLE_ID
        FROM `{TABLE_SOLUTION}` s
        LEFT JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY` c
            ON c.ID_COMPANY = s.ID_COMPANY
        WHERE s.ID_SOLUTION = @solution_id
        LIMIT 1
    """, {"solution_id": solution_id})

    solution = solution_rows[0] if solution_rows else {}

    stats_rows = query_bq(f"""
        SELECT
            COALESCE(total, 0) AS NB_ANALYSES,
            COALESCE(last_30_days, 0) AS DELTA_30D
        FROM `{VIEW_STATS_SOLUTION}`
        WHERE id_solution = @solution_id
        LIMIT 1
    """, {"solution_id": solution_id})

    stats = stats_rows[0] if stats_rows else {}

    items = get_solution_feed(
        solution_id,
        limit,
        offset,
        user_id,
        universe_id
    )

    return {
        "id_solution": solution_id,
        "name": solution.get("NAME"),
        "company_name": solution.get("COMPANY_NAME"),
        "media_logo_rectangle_id": solution.get("MEDIA_LOGO_RECTANGLE_ID"),
        "nb_analyses": stats.get("NB_ANALYSES", 0),
        "delta_30d": stats.get("DELTA_30D", 0),
        "items": items
    }


# ============================================================
# MAPPER
# ============================================================

def _map_feed_row(r: Dict):

    def fmt(dt):
        return dt.isoformat() if dt else None

    return {
        "id": r.get("id"),
        "type": r.get("type"),
        "title": r.get("title"),
        "excerpt": r.get("excerpt"),
        "published_at": fmt(r.get("published_at")),
        "news_type": None,
        "topics": r.get("topics") or [],
        "companies": r.get("companies") or [],
        "solutions": r.get("solutions") or [],
    }
