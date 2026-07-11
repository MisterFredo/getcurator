from typing import Dict, List

from utils.bigquery_utils import query_bq

from core.numbers.insight_service import (
    generate_numbers_insight,
    get_numbers_by_ids,
)

from core.mcp.suggestions import build_suggestions
from config import BQ_PROJECT, BQ_DATASET


TABLE_COMPANY_ALIAS = (
    f"{BQ_PROJECT}.{BQ_DATASET}.V_NUMBERS_ENRICHED"
)


# ============================================================
# 🔎 PARSE INTENTION NUMBERS
# ============================================================

def _detect_numbers_filter(query: str) -> List[str]:

    q = query.lower()

    mapping = {
        "MARKET_SHARE": ["part de marche", "market share"],
        "REVENUE": ["revenu", "ca", "chiffre d affaire"],
        "GROWTH": ["croissance", "growth"],
        "USERS": ["utilisateur", "users", "audience"],
        "VOLUME": ["volume", "gmv"],
        "PERFORMANCE": ["cpm", "cpc", "ctr", "roi"]
    }

    detected = []

    for category, keywords in mapping.items():
        if any(k in q for k in keywords):
            detected.append(category)

    return detected


# ============================================================
# 1. SÉLECTION IDs
# ============================================================

def _get_latest_numbers_ids(entity: Dict, limit: int = 30) -> List[str]:

    label = entity.get("label")
    entity_type = entity.get("type")

    if entity_type in ["company", "topic", "solution"] and label:

        sql = f"""
        SELECT ID_NUMBER
        FROM `{TABLE_NUMBERS}`
        WHERE LOWER(entity_label) = LOWER(@label)
        ORDER BY created_at DESC
        LIMIT @limit
        """

        params = {
            "label": label,
            "limit": limit
        }

    else:

        sql = f"""
        SELECT ID_NUMBER
        FROM `{TABLE_NUMBERS}`
        ORDER BY created_at DESC
        LIMIT @limit
        """

        params = {
            "limit": limit
        }

    rows = query_bq(sql, params)

    return [r["ID_NUMBER"] for r in rows]


# ============================================================
# 2. TRI
# ============================================================

def _sort_numbers(numbers: List[Dict]) -> List[Dict]:

    priority = {
        "MARKET_SHARE": 1,
        "REVENUE": 2,
        "GROWTH": 3,
        "USERS": 4,
        "VOLUME": 5,
        "PERFORMANCE": 6,
        "OTHER": 7
    }

    return sorted(
        numbers,
        key=lambda x: priority.get(x.get("category"), 99)
    )


# ============================================================
# 3. GROUP
# ============================================================

def _group_numbers_by_segment(numbers: List[Dict]) -> Dict:

    grouped = {}

    for n in numbers:
        segment = n.get("segment") or "Other"

        grouped.setdefault(segment, []).append(n)

    return grouped


# ============================================================
# HANDLER
# ============================================================

def handle_numbers(entity: Dict, user_query: str) -> Dict:

    # ----------------------------------------------------------
    # 1. INTENTION (CRITIQUE)
    # ----------------------------------------------------------
    filters = _detect_numbers_filter(user_query)

    # ----------------------------------------------------------
    # 2. IDS
    # ----------------------------------------------------------
    ids = _get_latest_numbers_ids(entity)

    if not ids:
        return {
            "status": "empty",
            "intent": "numbers",
            "entity": entity,
            "answer": {
                "items": [],
                "grouped": {},
                "text": "Aucun chiffre disponible",
                "nb_numbers": 0
            },
            "meta": {
                "suggestions": []
            }
        }

    # ----------------------------------------------------------
    # 3. DATA
    # ----------------------------------------------------------
    numbers = get_numbers_by_ids(ids)

    # ----------------------------------------------------------
    # 4. FILTRAGE INTELLIGENT
    # ----------------------------------------------------------
    if filters:
        numbers_filtered = [
            n for n in numbers
            if n.get("category") in filters
        ]

        # fallback si filtre trop strict
        if numbers_filtered:
            numbers = numbers_filtered

    # ----------------------------------------------------------
    # 5. TRI
    # ----------------------------------------------------------
    numbers_sorted = _sort_numbers(numbers)

    # ----------------------------------------------------------
    # 6. GROUP
    # ----------------------------------------------------------
    numbers_grouped = _group_numbers_by_segment(numbers_sorted)

    # ----------------------------------------------------------
    # 7. INSIGHT
    # ----------------------------------------------------------
    insight = generate_numbers_insight(numbers_grouped)

    # ----------------------------------------------------------
    # 8. SUGGESTIONS
    # ----------------------------------------------------------
    suggestions = build_suggestions(
        intent="numbers",
        entity=entity,
        items=numbers_sorted
    )

    # ----------------------------------------------------------
    # 9. RESPONSE
    # ----------------------------------------------------------
    return {
        "status": "ok",
        "intent": "numbers",
        "entity": entity,
        "answer": {
            "items": numbers_sorted,
            "grouped": numbers_grouped,
            "text": insight,
            "nb_numbers": len(numbers_sorted)
        },
        "meta": {
            "suggestions": suggestions
        }
    }
