from typing import Optional, List, Dict
from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq

TABLE_NUMBERS = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS"
TABLE_NUMBERS_COMPANY = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS_COMPANY"
TABLE_NUMBERS_TOPIC = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS_TOPIC"
TABLE_NUMBERS_SOLUTION = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS_SOLUTION"


# ============================================================
# BASIC QUALITY
# ============================================================

def check_basic_quality(
    value: float,
    id_number_type: str,
    zone: str,
    period: str,
    company_ids: Optional[List[str]] = None,
):

    if value is None:
        return {"status": "invalid_value"}

    if value <= 0:
        return {"status": "warning", "reason": "value <= 0"}

    if company_ids:

        rows = query_bq(f"""
            SELECT 1
            FROM `{TABLE_NUMBERS}` n
            JOIN `{TABLE_NUMBERS_COMPANY}` c
              ON n.ID_NUMBER = c.ID_NUMBER
            WHERE c.ID_COMPANY IN UNNEST(@company_ids)
            AND n.VALUE = @value
            AND n.ID_NUMBER_TYPE = @type
            AND n.ZONE = @zone
            AND n.PERIOD = @period
            LIMIT 1
        """, {
            "company_ids": company_ids,
            "value": value,
            "type": id_number_type,
            "zone": zone,
            "period": period,
        })

        if rows:
            return {"status": "duplicate"}

    return {"status": "ok"}


# ============================================================
# COHERENCE
# ============================================================

def check_number_coherence(
    value: float,
    id_number_type: str,
    zone: str,
    period: str,
    company_id: Optional[str] = None,
    topic_id: Optional[str] = None,
    solution_id: Optional[str] = None,
):

    SCALE_FACTORS = {
        None: 1,
        "thousand": 1_000,
        "million": 1_000_000,
        "billion": 1_000_000_000,
    }

    if not (company_id or topic_id or solution_id):
        return {"status": "no_entity"}

    if company_id:
        join = f"JOIN `{TABLE_NUMBERS_COMPANY}` rel ON n.ID_NUMBER = rel.ID_NUMBER"
        condition = "rel.ID_COMPANY = @entity_id"

    elif topic_id:
        join = f"JOIN `{TABLE_NUMBERS_TOPIC}` rel ON n.ID_NUMBER = rel.ID_NUMBER"
        condition = "rel.ID_TOPIC = @entity_id"

    else:
        join = f"JOIN `{TABLE_NUMBERS_SOLUTION}` rel ON n.ID_NUMBER = rel.ID_NUMBER"
        condition = "rel.ID_SOLUTION = @entity_id"

    rows = query_bq(f"""
        SELECT n.VALUE, n.SCALE
        FROM `{TABLE_NUMBERS}` n
        {join}
        WHERE {condition}
        AND n.ID_NUMBER_TYPE = @type_id
        AND n.ZONE = @zone
        AND n.PERIOD = @period
    """, {
        "entity_id": company_id or topic_id or solution_id,
        "type_id": id_number_type,
        "zone": zone,
        "period": period,
    })

    values = [
        r["VALUE"] * SCALE_FACTORS.get(r.get("SCALE"), 1)
        for r in rows
        if r.get("VALUE") is not None
    ]

    if len(values) < 2:
        return {"status": "no_baseline"}

    min_v = min(values)
    max_v = max(values)

    if min_v == 0:
        return {"status": "invalid_baseline"}

    ratio = max_v / min_v

    if ratio > 2:
        return {"status": "high_inconsistency", "ratio": ratio}
    elif ratio > 1.3:
        return {"status": "medium_inconsistency", "ratio": ratio}

    return {"status": "ok", "ratio": ratio}
