from typing import List, Dict, Optional

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq

from core.curator.service import build_user_filter


# ============================================================
# TABLES / VIEWS
# ============================================================

VIEW_CONTENT = f"{BQ_PROJECT}.{BQ_DATASET}.V_CONTENT_ENRICHED"
TABLE_BACKLOG = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS_BACKLOG"


# ============================================================
# SEARCH — CONTEXTUAL (🔥 CORE)
# ============================================================

def search_curator_numbers(
    query: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    user_id: Optional[str] = None,
    universe_id: Optional[str] = None,
) -> List[Dict]:

    query = (query or "").strip()

    # ============================================================
    # 🌍 UNIVERSE FILTER
    # ============================================================

    universe_filter = ""
    if universe_id:
        universe_filter = """
        AND EXISTS (
            SELECT 1
            FROM UNNEST(c.universes) u
            WHERE u.id_universe = @universe_id
        )
        """

    # ============================================================
    # 🔎 SEARCH LOGIC (🔥 CONTENT FIRST)
    # ============================================================

    search_clause = ""

    if query:

        search_clause = """
        AND (
            -- 🔵 TEXTE
            LOWER(c.title) LIKE LOWER(CONCAT('%', @query, '%'))
            OR LOWER(c.excerpt) LIKE LOWER(CONCAT('%', @query, '%'))

            -- 🟢 COMPANY
            OR EXISTS (
                SELECT 1
                FROM UNNEST(c.companies) co
                WHERE LOWER(co.name) LIKE LOWER(CONCAT('%', @query, '%'))
            )

            -- 🔵 SOLUTION
            OR EXISTS (
                SELECT 1
                FROM UNNEST(c.solutions) s
                WHERE LOWER(s.name) LIKE LOWER(CONCAT('%', @query, '%'))
            )

            -- 🟣 CONCEPTS (🔥 IMPORTANT)
            OR EXISTS (
                SELECT 1
                FROM UNNEST(c.concepts) con
                WHERE LOWER(con.title) LIKE LOWER(CONCAT('%', @query, '%'))
            )
        )
        """

    # ============================================================
    # MAIN QUERY
    # ============================================================

    sql = f"""
    SELECT
        b.ID_BACKLOG,
        b.ID_CONTENT,

        c.title AS context_title,
        c.published_at,

        -- 🔢 NUMBER
        b.LABEL,
        SAFE_CAST(b.VALUE AS FLOAT64) AS VALUE,
        b.UNIT,
        b.MARKET AS zone,
        b.PERIOD,
        b.ACTOR

    FROM `{VIEW_CONTENT}` c

    JOIN `{TABLE_BACKLOG}` b
      ON b.ID_CONTENT = c.id_content

    WHERE 1=1

    {search_clause}

    -- 🔐 USER FILTER
    {build_user_filter("c") if user_id else ""}

    -- 🌍 UNIVERSE FILTER
    {universe_filter}

    -- 🔥 CLEAN BACKLOG
    AND (b.DECISION IS NULL)

    ORDER BY c.published_at DESC

    LIMIT @limit
    OFFSET @offset
    """

    params = {
        "query": query,
        "limit": limit,
        "offset": offset,
        "user_id": user_id,
        "universe_id": universe_id,
    }

    rows = query_bq(sql, params)

    return [_map_number_row(r) for r in rows]


# ============================================================
# LATEST (NO QUERY)
# ============================================================

def latest_curator_numbers(
    limit: int = 50,
    offset: int = 0,
    user_id: Optional[str] = None,
    universe_id: Optional[str] = None,
) -> List[Dict]:

    return search_curator_numbers(
        query=None,
        limit=limit,
        offset=offset,
        user_id=user_id,
        universe_id=universe_id,
    )


# ============================================================
# ENTITY (V2 PASSTHROUGH)
# ============================================================

def get_curator_numbers_by_entity(
    entity_type: str,
    entity_id: str,
    limit: Optional[int] = None,
):

    from core.numbers.search import get_numbers_for_entity

    return get_numbers_for_entity(
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit,
    )


# ============================================================
# MAPPER
# ============================================================

def _map_number_row(r: Dict) -> Dict:

    def fmt(dt):
        return dt.isoformat() if dt else None

    return {
        "id": r.get("ID_BACKLOG"),
        "type": "number_backlog",

        # 🔢 NUMBER
        "label": r.get("LABEL"),
        "value": r.get("VALUE"),
        "unit": r.get("UNIT"),
        "zone": r.get("zone"),
        "period": r.get("PERIOD"),
        "actor": r.get("ACTOR"),

        # 🧠 CONTEXT
        "context_title": r.get("context_title"),
        "published_at": fmt(r.get("published_at")),
    }
