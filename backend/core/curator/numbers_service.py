from typing import List, Dict, Optional

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq

from core.curator.service import build_user_filter


# ============================================================
# TABLES / VIEWS
# ============================================================

VIEW_CONTENT = f"{BQ_PROJECT}.{BQ_DATASET}.V_CONTENT_ENRICHED"
TABLE_BACKLOG = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS_BACKLOG"
TABLE_CONTENT_CONCEPT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_CONCEPT"


# ============================================================
# SEARCH — CONTEXTUAL (🔥 CORE)
# ============================================================

def search_curator_numbers(
    query: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    user_id: Optional[str] = None,
    universe_id: Optional[str] = None,
    concept_ids: Optional[List[str]] = None,
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
    # 🧠 CONCEPT FILTER (STRUCTURANT)
    # ============================================================

    concept_filter = ""
    if concept_ids:
        concept_filter = f"""
        AND EXISTS (
            SELECT 1
            FROM `{TABLE_CONTENT_CONCEPT}` cc
            WHERE cc.ID_CONTENT = c.id_content
              AND cc.ID_CONCEPT IN UNNEST(@concept_ids)
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

            -- 🟣 CONCEPTS
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
        b.MARKET AS ZONE,
        b.PERIOD,
        b.ACTOR

    FROM `{VIEW_CONTENT}` c

    JOIN `{TABLE_BACKLOG}` b
      ON b.ID_CONTENT = c.id_content

    WHERE 1=1

    {search_clause}

    -- 🔐 USER FILTER
    {build_user_filter("c") if user_id else ""}

    -- 🌍 UNIVERSE
    {universe_filter}

    -- 🧠 CONCEPTS
    {concept_filter}

    -- 🔥 BACKLOG CLEAN
    AND b.DECISION IS NULL

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
        "concept_ids": concept_ids,
    }

    rows = query_bq(sql, params)

    return [_map_number_row(r) for r in rows]


# ============================================================
# LATEST
# ============================================================

def latest_curator_numbers(
    limit: int = 50,
    offset: int = 0,
    user_id: Optional[str] = None,
    universe_id: Optional[str] = None,
    concept_ids: Optional[List[str]] = None,
) -> List[Dict]:

    return search_curator_numbers(
        query=None,
        limit=limit,
        offset=offset,
        user_id=user_id,
        universe_id=universe_id,
        concept_ids=concept_ids,
    )


# ============================================================
# ENTITY (V2 ONLY — OFFICIAL NUMBERS)
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
# MAPPER (🔥 COMPAT FRONT)
# ============================================================

def _map_number_row(r: Dict) -> Dict:

    def fmt(dt):
        return dt.isoformat() if dt else None

    return {
        # 🔥 CRUCIAL → compat NumberCard
        "ID_NUMBER": r.get("ID_BACKLOG"),

        "LABEL": r.get("LABEL"),
        "VALUE": r.get("VALUE"),
        "UNIT": r.get("UNIT"),
        "SCALE": None,

        "ZONE": r.get("ZONE"),
        "PERIOD": r.get("PERIOD"),

        # 🔥 fallback actor → affichage badges
        "ENTITIES": [
            {
                "ENTITY_TYPE": "actor",
                "ENTITY_LABEL": r.get("ACTOR"),
            }
        ] if r.get("ACTOR") else [],

        "TYPE": None,
        "CATEGORY": None,

        # 🧠 CONTEXTE
        "context_title": r.get("context_title"),
        "ID_CONTENT": r.get("ID_CONTENT"),
        "published_at": fmt(r.get("published_at")),
    }
