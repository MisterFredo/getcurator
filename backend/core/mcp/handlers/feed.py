from typing import Dict, List

from core.feed.service import search_text
from core.mcp.suggestions import build_suggestions
from utils.bigquery_utils import query_bq

TABLE_COMPANY_ALIAS = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"
)


# ============================================================
# FETCH LATEST (AVEC URL)
# ============================================================

def _get_latest_items(limit: int = 10) -> List[Dict]:

    sql = f"""
    SELECT
        c.ID_CONTENT as id,
        'analysis' as type,
        c.TITLE,
        c.EXCERPT,
        c.PUBLISHED_AT,
        NULL as url
    FROM `{TABLE_CONTENT}` c
    WHERE c.STATUS = 'PUBLISHED'
      AND c.IS_ACTIVE = TRUE

    ORDER BY PUBLISHED_AT DESC
    LIMIT {limit}
    """

    rows = query_bq(sql)

    return [_normalize_item(r) for r in rows]


# ============================================================
# NORMALISATION (ROBUSTE)
# ============================================================

def _normalize_item(r: Dict) -> Dict:

    return {
        "id": r.get("id") or r.get("ID_NEWS") or r.get("ID_CONTENT"),
        "type": r.get("type"),
        "title": r.get("title") or r.get("TITLE"),
        "excerpt": r.get("excerpt") or r.get("EXCERPT"),
        "published_at": r.get("published_at") or r.get("PUBLISHED_AT"),
        "url": r.get("url"),  # 🔥 clé UX
    }


# ============================================================
# HANDLER
# ============================================================

def handle_feed(entity: Dict, user_query: str) -> Dict:

    entity_label = entity.get("label")
    query = user_query.strip().lower() if user_query else ""

    # ----------------------------------------------------------
    # MODE GLOBAL (arrivée utilisateur)
    # ----------------------------------------------------------

    if not entity_label and (
        not query or "quoi de neuf" in query or "actualité" in query
    ):
        rows = _get_latest_items(limit=10)

    # ----------------------------------------------------------
    # MODE SEARCH (entity ou texte libre)
    # ----------------------------------------------------------

    else:
        search_query = entity_label or user_query
        raw_rows = search_text(query=search_query, limit=10)
        rows = [_normalize_item(r) for r in raw_rows]

    # ----------------------------------------------------------
    # EMPTY
    # ----------------------------------------------------------

    if not rows:
        return {
            "status": "empty",
            "intent": "feed",
            "entity": entity,
            "answer": {
                "items": []
            }
        }

    # ----------------------------------------------------------
    # 🔥 SUGGESTIONS DYNAMIQUES
    # ----------------------------------------------------------

    suggestions = build_suggestions(
        intent="feed",
        entity=entity,
        items=rows
    )

    # ----------------------------------------------------------
    # RESPONSE
    # ----------------------------------------------------------

    return {
        "status": "ok",
        "intent": "feed",
        "entity": entity,
        "answer": {
            "items": rows
        },
        "meta": {
            "suggestions": suggestions
        }
    }
