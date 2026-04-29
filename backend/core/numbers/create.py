import uuid
from typing import Dict

from google.cloud import bigquery

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq, get_bigquery_client

from core.numbers.quality import (
    check_basic_quality,
    check_number_coherence,
)

from core.numbers.parsing import _extract_unit_scale

# ============================================================
# TABLES
# ============================================================

TABLE_NUMBERS = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS"
TABLE_NUMBERS_TYPES = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS_TYPE"

TABLE_NUMBERS_COMPANY = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS_COMPANY"
TABLE_NUMBERS_TOPIC = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS_TOPIC"
TABLE_NUMBERS_SOLUTION = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS_SOLUTION"


# ============================================================
# HELPERS
# ============================================================

def _now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def normalize_number_payload(data: Dict) -> Dict:

    value = data.get("value")
    zone = (data.get("zone") or "").strip().upper()
    period = (data.get("period") or "").strip()

    try:
        value = float(value)
    except:
        value = None

    unit_raw = data.get("unit")
    unit, scale = _extract_unit_scale(unit_raw)

    return {
        "label": data.get("label"),
        "value": value,
        "unit": unit,
        "scale": data.get("scale") or scale,
        "id_number_type": data.get("id_number_type"),
        "type": data.get("type"),  # 🔥 important pour LLM
        "zone": zone,
        "period": period,
        "source_id": data.get("source_id"),
        "confidence": data.get("confidence"),
        "notes": data.get("notes"),
        "company_ids": data.get("company_ids") or [],
        "topic_ids": data.get("topic_ids") or [],
        "solution_ids": data.get("solution_ids") or [],
    }


# ============================================================
# TYPE MAPPING
# ============================================================

def map_type_to_id(type_value: str):

    if not type_value:
        return None

    rows = query_bq(f"""
        SELECT ID_TYPE, TYPE
        FROM `{TABLE_NUMBERS_TYPES}`
        WHERE IS_ACTIVE = TRUE
    """)

    mapping = {
        r["TYPE"].lower(): r["ID_TYPE"]
        for r in rows
    }

    return mapping.get(type_value.lower())


# ============================================================
# FIND EXISTING
# ============================================================

def find_existing_numbers(
    id_number_type,
    zone,
    period,
    company_ids=None,
    topic_ids=None,
    solution_ids=None,
):

    if not (company_ids or topic_ids or solution_ids):
        return []

    if company_ids:
        join = f"JOIN `{TABLE_NUMBERS_COMPANY}` rel ON n.ID_NUMBER = rel.ID_NUMBER"
        condition = "rel.ID_COMPANY IN UNNEST(@entity_ids)"
        entity_ids = company_ids

    elif topic_ids:
        join = f"JOIN `{TABLE_NUMBERS_TOPIC}` rel ON n.ID_NUMBER = rel.ID_NUMBER"
        condition = "rel.ID_TOPIC IN UNNEST(@entity_ids)"
        entity_ids = topic_ids

    else:
        join = f"JOIN `{TABLE_NUMBERS_SOLUTION}` rel ON n.ID_NUMBER = rel.ID_NUMBER"
        condition = "rel.ID_SOLUTION IN UNNEST(@entity_ids)"
        entity_ids = solution_ids

    return query_bq(f"""
        SELECT ID_NUMBER, VALUE, SCALE, UNIT
        FROM `{TABLE_NUMBERS}` n
        {join}
        WHERE {condition}
        AND n.ID_NUMBER_TYPE = @type_id
        AND n.ZONE = @zone
        AND n.PERIOD = @period
    """, {
        "entity_ids": entity_ids,
        "type_id": id_number_type,
        "zone": zone,
        "period": period,
    })

# ============================================================
# INSERT RELATIONS
# ============================================================

def _insert_relations(id_number, company_ids, topic_ids, solution_ids):

    client = get_bigquery_client()

    if company_ids:
        client.load_table_from_json([
            {"ID_NUMBER": id_number, "ID_COMPANY": cid, "CREATED_AT": _now()}
            for cid in company_ids
        ], TABLE_NUMBERS_COMPANY).result()

    if topic_ids:
        client.load_table_from_json([
            {"ID_NUMBER": id_number, "ID_TOPIC": tid, "CREATED_AT": _now()}
            for tid in topic_ids
        ], TABLE_NUMBERS_TOPIC).result()

    if solution_ids:
        client.load_table_from_json([
            {"ID_NUMBER": id_number, "ID_SOLUTION": sid, "CREATED_AT": _now()}
            for sid in solution_ids
        ], TABLE_NUMBERS_SOLUTION).result()

# ============================================================
# CREATE (FIX COHERENCE + DUPLICATE)
# ============================================================

def create_number(data) -> Dict:

    if hasattr(data, "dict"):
        data = data.dict()

    payload = normalize_number_payload(data)

    # ============================================================
    # TYPE MAPPING
    # ============================================================

    if not payload.get("id_number_type") and payload.get("type"):
        mapped = map_type_to_id(payload.get("type"))

        if not mapped:
            return {
                "id_number": None,
                "quality": {"status": "invalid_type"}
            }

        payload["id_number_type"] = mapped

    # ============================================================
    # EXISTING
    # ============================================================

    existing = find_existing_numbers(
        payload["id_number_type"],
        payload["zone"],
        payload["period"],
        payload["company_ids"],
        payload["topic_ids"],
        payload["solution_ids"],
    )

    # 🔥 DUPLICATE ROBUSTE
    for e in existing:

        existing_value = e.get("VALUE")
        existing_scale = e.get("SCALE")

        if existing_value == payload["value"] and existing_scale == payload["scale"]:
            return {
                "id_number": None,
                "quality": {"status": "duplicate_exact"}
            }

    # ============================================================
    # QUALITY
    # ============================================================

    quality = check_basic_quality(
        payload["value"],
        payload["id_number_type"],
        payload["zone"],
        payload["period"],
        payload["company_ids"],
    )

    # 🔥 COHERENCE CORRECTE
    coherence = check_number_coherence(
        value=payload["value"],
        id_number_type=payload["id_number_type"],
        zone=payload["zone"],
        period=payload["period"],
        company_id=payload["company_ids"][0] if payload["company_ids"] else None,
        topic_id=payload["topic_ids"][0] if payload["topic_ids"] else None,
        solution_id=payload["solution_ids"][0] if payload["solution_ids"] else None,
    )

    if coherence.get("status") == "high_inconsistency":
        return {
            "id_number": None,
            "quality": coherence
        }

    # ============================================================
    # INSERT
    # ============================================================

    id_number = str(uuid.uuid4())

    row = [{
        "ID_NUMBER": id_number,
        "LABEL": payload.get("label"),
        "VALUE": payload.get("value"),
        "UNIT": payload.get("unit"),
        "SCALE": payload.get("scale"),
        "ID_NUMBER_TYPE": payload.get("id_number_type"),
        "ZONE": payload.get("zone"),
        "PERIOD": payload.get("period"),
        "ID_SOURCE": payload.get("source_id"),
        "CONFIDENCE": payload.get("confidence"),
        "NOTES": payload.get("notes"),
        "CREATED_AT": _now(),
        "UPDATED_AT": _now(),
    }]

    client = get_bigquery_client()

    client.load_table_from_json(
        row,
        TABLE_NUMBERS,
        job_config=bigquery.LoadJobConfig(write_disposition="WRITE_APPEND"),
    ).result()

    _insert_relations(
        id_number,
        payload["company_ids"],
        payload["topic_ids"],
        payload["solution_ids"],
    )

    return {
        "id_number": id_number,
        "quality": {
            **quality,
            "coherence": coherence.get("status"),
        }
    }
