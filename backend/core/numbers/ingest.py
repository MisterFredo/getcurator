from typing import List, Dict

from core.numbers.create import create_number
from utils.bigquery_utils import query_bq
from config import BQ_PROJECT, BQ_DATASET


# ============================================================
# MAP ACTOR → COMPANY_ID
# ============================================================

def _map_actor_to_company_ids(actor: str) -> List[str]:

    if not actor or actor.lower() == "non précisé":
        return []

    rows = query_bq(f"""
        SELECT ID_COMPANY
        FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY`
        WHERE LOWER(NAME) = LOWER(@name)
        LIMIT 3
    """, {"name": actor})

    return [r["ID_COMPANY"] for r in rows]


# ============================================================
# MAIN INGEST
# ============================================================

def ingest_numbers_from_content(
    chiffres: List[Dict],
    source_id: str = None,
):

    results = []

    for c in chiffres:

        payload = {
            "label": c.get("label"),
            "value": c.get("value"),
            "unit": c.get("unit"),
            "scale": c.get("scale"),
            "zone": c.get("zone"),
            "period": c.get("period"),
            "type": c.get("type"),  # 🔥 clé
            "source_id": source_id,
            "company_ids": _map_actor_to_company_ids(c.get("actor")),
        }

        result = create_number(payload)

        results.append(result)

    return results
