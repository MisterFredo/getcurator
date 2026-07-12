from typing import Dict, List

from utils.bigquery_utils import query_bq

from core.curator.entity_service import get_topic_view
from core.feed.service import search_text
from core.numbers.insight_service import get_numbers_by_ids
from core.mcp.suggestions import build_suggestions
from config import BQ_PROJECT, BQ_DATASET


# ============================================================
# CONSTANTES
# ============================================================


TABLE_COMPANY_ALIAS = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOPIC"
)

TABLE_COMPANY_ALIAS = (
    f"{BQ_PROJECT}.{BQ_DATASET}.V_NUMBERS_ENRICHED"
)


# ============================================================
# 1. RESOLVE TOPIC ID (ROBUST)
# ============================================================

def _get_topic_id(label: str):

    sql = """
    SELECT ID_TOPIC
    FROM `adex-5555.RATECARD_PROD.RATECARD_TOPIC`
    WHERE LOWER(@label) LIKE CONCAT('%', LOWER(LABEL), '%')
    LIMIT 1
    """

    rows = query_bq(sql, {"label": label})

    return rows[0]["ID_TOPIC"] if rows else None


# ============================================================
# 2. LIST TOPICS (GUIDAGE)
# ============================================================

def _get_all_topics():

    sql = """
    SELECT LABEL
    FROM `adex-5555.RATECARD_PROD.RATECARD_TOPIC`
    ORDER BY LABEL
    """

    rows = query_bq(sql)

    return [r["LABEL"] for r in rows]


# ============================================================
# 3. NUMBERS IDS
# ============================================================

def _get_topic_numbers_ids(label: str, limit: int = 6) -> List[str]:

    sql = """
    SELECT ID_NUMBER
    FROM `adex-5555.RATECARD_PROD.V_NUMBERS_ENRICHED`
    WHERE LOWER(entity_label) = LOWER(@label)
    ORDER BY created_at DESC
    LIMIT @limit
    """

    rows = query_bq(sql, {
        "label": label,
        "limit": limit
    })

    return [r["ID_NUMBER"] for r in rows]


# ============================================================
# 4. HANDLER
# ============================================================

def handle_topic(entity: Dict) -> Dict:
    """
    Handler MCP pour :
    → comprendre un sujet (lecture marché)
    """

    label = entity.get("label")

    if not label:
        return {
            "status": "error",
            "intent": "topic",
            "message": "Sujet non reconnu"
        }

    # ----------------------------------------------------------
    # 1. RESOLVE
    # ----------------------------------------------------------
    topic_id = _get_topic_id(label)

    # ----------------------------------------------------------
    # 🔥 FALLBACK (SUJET NON GOUVERNÉ)
    # ----------------------------------------------------------
    if not topic_id:

        feed_raw = search_text(query=label, limit=10) or []

        feed = [
            f for f in feed_raw
            if f.get("type") in ["analysis", "news"]
        ][:8]

        for item in feed:
            if item.get("type") == "news":
                item["url"] = f"/news/{item.get('id')}"
            else:
                item["url"] = f"/analysis/{item.get('id')}"

        suggestions = build_suggestions(
            intent="search",
            entity={"label": label},
            items=feed
        )

        return {
            "status": "fallback",
            "intent": "topic",
            "entity": entity,
            "answer": {
                "text": f"{label} n'est pas un sujet analysé en profondeur.\nVoici les contenus disponibles :",
                "items": feed,
                "available_topics": _get_all_topics()
            },
            "meta": {
                "suggestions": suggestions
            }
        }

    # ----------------------------------------------------------
    # 2. VIEW (SOURCE DE VÉRITÉ)
    # ----------------------------------------------------------
    view = get_topic_view(topic_id, limit=10)
    items = view.get("items", []) or []

    # ----------------------------------------------------------
    # 3. FEED (FILTRÉ)
    # ----------------------------------------------------------
    feed = [
        i for i in items
        if i.get("type") in ["analysis", "news"]
    ][:3]

    for item in feed:
        if item.get("type") == "news":
            item["url"] = f"/news/{item.get('id')}"
        else:
            item["url"] = f"/analysis/{item.get('id')}"

    # ----------------------------------------------------------
    # 5. NUMBERS
    # ----------------------------------------------------------
    number_ids = _get_topic_numbers_ids(label, limit=6)
    numbers = get_numbers_by_ids(number_ids) if number_ids else []


    # ----------------------------------------------------------
    # 7. SUGGESTIONS
    # ----------------------------------------------------------
    suggestions = build_suggestions(
        intent="topic",
        entity=entity,
        items=feed
    )

    # ----------------------------------------------------------
    # 8. RESPONSE (STRUCTURE PRODUIT)
    # ----------------------------------------------------------
    return {
        "status": "ok",
        "intent": "topic",
        "entity": entity,
        "answer": {
            "name": view.get("label"),
            "description": view.get("description"),

            # 🔥 signal stratégique
            "radar": radar,

            # 🔥 compréhension marché
            "analysis": analysis_text,

            # 🔥 preuve data
            "numbers": numbers,

            # 🔥 contexte
            "latest_contents": feed,

            # 🔥 bonus UX
            "stats": {
                "nb_analyses": view.get("nb_analyses"),
                "delta_30d": view.get("delta_30d")
            }
        },
        "meta": {
            "suggestions": suggestions
        }
    }
