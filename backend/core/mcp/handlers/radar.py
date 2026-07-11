from typing import Dict, List

from utils.bigquery_utils import query_bq

from core.radar.insight_service import (
    generate_radar_insight,
)
from config import BQ_PROJECT, BQ_DATASET

# ============================================================
# CONSTANTE
# ============================================================

TABLE_COMPANY_ALIAS = (
    f"{BQ_PROJECT}.{BQ_DATASET}.V_RADARD_ENRICHED"
)


# ============================================================
# 1. SÉLECTION AUTOMATIQUE DES RADARS
# ============================================================

def _get_latest_radar_ids(entity: Dict, limit: int = 5) -> List[str]:
    """
    Sélection automatique des radars pertinents.
    """

    entity_label = entity.get("label")
    entity_type = entity.get("type")

    if entity_type in ["company", "topic", "solution"] and entity_label:

        sql = f"""
        SELECT ID_INSIGHT
        FROM `{TABLE_RADAR}`
        WHERE LOWER(entity_label) = LOWER("{entity_label}")
        ORDER BY YEAR DESC, PERIOD DESC
        LIMIT {limit}
        """

    else:
        # fallback global
        sql = f"""
        SELECT ID_INSIGHT
        FROM `{TABLE_RADAR}`
        ORDER BY YEAR DESC, PERIOD DESC
        LIMIT {limit}
        """

    rows = query_bq(sql)

    return [r["ID_INSIGHT"] for r in rows]


# ============================================================
# 2. HANDLER PRINCIPAL
# ============================================================

def handle_radar(entity: Dict) -> Dict:
    """
    Handler MCP pour :
    → comprendre les dynamiques de marché
    """

    # ----------------------------------------------------------
    # 1. Sélection
    # ----------------------------------------------------------
    ids = _get_latest_radar_ids(entity)

    if not ids:
        return {
            "status": "empty",
            "intent": "radar",
            "entity": entity,
            "answer": {
                "text": "Aucune dynamique disponible."
            }
        }

    # ----------------------------------------------------------
    # 2. Pipeline radar (EXISTANT)
    # ----------------------------------------------------------
    insight = generate_radar_insight(ids)

    # ----------------------------------------------------------
    # 3. Suggestions
    # ----------------------------------------------------------
    suggestions = [
        "Retail Media",
        "CTV",
        "Amazon",
        "Netflix"
    ]

    # ----------------------------------------------------------
    # 4. Réponse
    # ----------------------------------------------------------
    return {
        "status": "ok",
        "intent": "radar",
        "entity": entity,
        "answer": {
            "title": "Dynamiques du marché",
            "text": insight,
            "nb_radars": len(ids)
        },
        "meta": {
            "suggestions": suggestions
        }
    }
