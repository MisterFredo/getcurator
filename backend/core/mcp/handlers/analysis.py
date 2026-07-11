from typing import Dict, List

from core.feed.service import search_text
from core.insight.service import run_insight_pipeline
from utils.bigquery_utils import query_bq


TABLE_COMPANY_ALIAS = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"
)


# ============================================================
# FETCH LATEST ANALYSES (GLOBAL)
# ============================================================

def _get_latest_analysis_ids(limit: int = 10) -> List[str]:

    sql = f"""
    SELECT ID_CONTENT as id
    FROM `{TABLE_CONTENT}`
    WHERE STATUS = 'PUBLISHED'
      AND IS_ACTIVE = TRUE
    ORDER BY PUBLISHED_AT DESC
    LIMIT {limit}
    """

    rows = query_bq(sql)

    return [r["id"] for r in rows]


# ============================================================
# HANDLER
# ============================================================

def handle_analysis(entity: Dict, user_query: str) -> Dict:
    """
    Handler MCP pour :
    → comprendre ce qui se passe sur le marché
    """

    entity_label = entity.get("label")
    query = user_query.strip().lower() if user_query else ""

    # ----------------------------------------------------------
    # MODE GLOBAL (par défaut)
    # ----------------------------------------------------------

    if not entity_label and (
        not query or "quoi de neuf" in query or "actualité" in query
    ):
        ids = _get_latest_analysis_ids(limit=10)

    # ----------------------------------------------------------
    # MODE CIBLÉ
    # ----------------------------------------------------------

    else:
        search_query = entity_label or user_query

        rows = search_text(query=search_query, limit=10)

        ids = [
            r["id"]
            for r in rows
            if r.get("type") == "analysis"
        ]

    # ----------------------------------------------------------
    # EMPTY
    # ----------------------------------------------------------

    if not ids:
        return {
            "status": "empty",
            "intent": "analysis",
            "entity": entity,
            "answer": {
                "text": "Aucune analyse disponible.",
                "nb_contents": 0
            }
        }

    # ----------------------------------------------------------
    # PIPELINE INSIGHT (TON MOTEUR)
    # ----------------------------------------------------------

    result = run_insight_pipeline(ids)

    insight_text = result.get("insight", "")

    # ----------------------------------------------------------
    # SUGGESTIONS
    # ----------------------------------------------------------

    suggestions = [
        "Retail Media",
        "CTV",
        "Amazon",
        "Netflix"
    ]

    # ----------------------------------------------------------
    # RESPONSE
    # ----------------------------------------------------------

    return {
        "status": "ok",
        "intent": "analysis",
        "entity": entity,
        "answer": {
            "text": insight_text,
            "nb_contents": len(ids)
        },
        "meta": {
            "suggestions": suggestions
        }
    }
