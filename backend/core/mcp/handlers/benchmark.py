from typing import Dict

from core.curator.service import search
from core.mcp.suggestions import build_suggestions
from config import BQ_PROJECT, BQ_DATASET


# ============================================================
# PARSE QUERY
# ============================================================

def _parse_entities(query: str):

    q = query.lower().replace("versus", "vs")

    if " vs " not in q:
        return None, None

    parts = q.split("vs")

    if len(parts) != 2:
        return None, None

    return parts[0].strip(), parts[1].strip()


# ============================================================
# HANDLER
# ============================================================

def handle_benchmark(user_query: str) -> Dict:

    e1, e2 = _parse_entities(user_query)

    if not e1 or not e2:
        return {
            "status": "error",
            "intent": "benchmark",
            "message": "Comparaison non valide"
        }

    # ----------------------------------------------------------
    # SEARCH PAR ENTITÉ (SÉPARÉ)
    # ----------------------------------------------------------

    rows_1 = search(q=e1, limit=5) or []
    rows_2 = search(q=e2, limit=5) or []

    if not rows_1 and not rows_2:
        return {
            "status": "empty",
            "intent": "benchmark",
            "answer": {
                "text": f"Aucune donnée disponible pour comparer {e1} et {e2}",
                "items": []
            }
        }

    # ----------------------------------------------------------
    # ENRICHISSEMENT URL + TAG ENTITÉ
    # ----------------------------------------------------------

    for item in rows_1:
        item["entity"] = e1
        if item.get("type") == "news":
            item["url"] = f"/news/{item.get('id')}"
        else:
            item["url"] = f"/analysis/{item.get('id')}"

    for item in rows_2:
        item["entity"] = e2
        if item.get("type") == "news":
            item["url"] = f"/news/{item.get('id')}"
        else:
            item["url"] = f"/analysis/{item.get('id')}"

    # ----------------------------------------------------------
    # MERGE (mais structuré)
    # ----------------------------------------------------------

    rows = rows_1 + rows_2

    # ----------------------------------------------------------
    # SUGGESTIONS
    # ----------------------------------------------------------

    suggestions = build_suggestions(
        intent="benchmark",
        entity={"label": f"{e1} vs {e2}"},
        items=rows
    )

    # ----------------------------------------------------------
    # RESPONSE STRUCTURÉE
    # ----------------------------------------------------------

    return {
        "status": "ok",
        "intent": "benchmark",
        "entity": {
            "type": "comparison",
            "label": f"{e1} vs {e2}"
        },
        "answer": {
            "analysis": analysis_text,
            "items": rows,
            "breakdown": {
                e1: rows_1,
                e2: rows_2
            }
        },
        "meta": {
            "suggestions": suggestions
        }
    }
