import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional

from google.cloud import bigquery

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq, get_bigquery_client

from core.numbers.parsing import (
    parse_chiffres,
    get_raw_numbers,
    get_numbers_from_content,
)

from core.numbers.quality import (
    check_basic_quality,
    check_number_coherence,
)

from core.numbers.search import (
    search_numbers_service
    get_numbers_feed_service
    get_numbers_for_entity
)

from core.numbers.create import (
    create_number
    normalize_number_payload
    map_type_to_id
    find_existing_numbers
    _insert_relations
    _now
)

from core.numbers.create import (
    _map_actor_to_company_ids
    ingest_numbers_from_content
)

TABLE_NUMBERS = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS"

TABLE_NUMBERS_COMPANY = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS_COMPANY"
TABLE_NUMBERS_TOPIC = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS_TOPIC"
TABLE_NUMBERS_SOLUTION = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS_SOLUTION"
TABLE_NUMBERS_TYPES = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS_TYPE"
VIEW_NUMBERS = f"{BQ_PROJECT}.{BQ_DATASET}.V_NUMBERS_ENRICHED"
VIEW_NUMBERS_CARDS = f"{BQ_PROJECT}.{BQ_DATASET}.V_NUMBERS_CARDS"

# ============================================================
# ORDER (UX métier)
# ============================================================

CATEGORY_ORDER = [
    "VALUE",
    "PERFORMANCE",
    "AUDIENCE",
    "POSITION",
    "DYNAMICS",
    "STRUCTURE",
    "MONETIZATION",
]


# ============================================================
# HELPERS
# ============================================================

def _now():
    return datetime.now(timezone.utc).isoformat()


# ============================================================
# NORMALIZATION
# ============================================================

def _extract_unit_scale(unit_raw: str):
    u = (unit_raw or "").lower()

    if "%" in u:
        return "PERCENT", None
    if "€" in u or "eur" in u:
        if "billion" in u or "milliard" in u:
            return "EUR", "billion"
        if "million" in u:
            return "EUR", "million"
        if "thousand" in u or "k" in u:
            return "EUR", "thousand"
        return "EUR", None

    return unit_raw.upper() if unit_raw else None, None

# ============================================================
# LIST
# ============================================================

def list_numbers(limit: int = 400):

    return query_bq(f"""
        SELECT *
        FROM `{TABLE_NUMBERS}`
        ORDER BY CREATED_AT DESC
        LIMIT @limit
    """, {"limit": limit})


# ============================================================
# DELETE
# ============================================================

def delete_number_relations(id_number: str):

    query_bq(f"""
        DELETE FROM `{TABLE_NUMBERS_COMPANY}`
        WHERE ID_NUMBER = @id_number
    """, {"id_number": id_number})

    query_bq(f"""
        DELETE FROM `{TABLE_NUMBERS_TOPIC}`
        WHERE ID_NUMBER = @id_number
    """, {"id_number": id_number})

    query_bq(f"""
        DELETE FROM `{TABLE_NUMBERS_SOLUTION}`
        WHERE ID_NUMBER = @id_number
    """, {"id_number": id_number})


def delete_number(id_number: str):

    query_bq(f"""
        DELETE FROM `{TABLE_NUMBERS}`
        WHERE ID_NUMBER = @id_number
    """, {"id_number": id_number})


# ============================================================
# TYPES
# ============================================================

def get_number_types():

    rows = query_bq(f"""
        SELECT ID_TYPE, TYPE
        FROM `{TABLE_NUMBERS_TYPES}`
        WHERE IS_ACTIVE IS TRUE OR IS_ACTIVE IS NULL
        ORDER BY TYPE
    """)

    return [
        {
            "id": r["ID_TYPE"],
            "label": r["TYPE"],
        }
        for r in rows
    ]


