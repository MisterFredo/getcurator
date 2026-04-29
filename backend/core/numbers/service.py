from typing import Optional, List, Dict

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq

# ============================================================
# IMPORTS MÉTIERS
# ============================================================

from core.numbers.create import create_number
from core.numbers.parsing import (
    parse_chiffres,
    get_numbers_from_content,
    get_raw_numbers,
)
from core.numbers.quality import check_number_coherence
from core.numbers.search import (
    search_numbers_service,
    get_numbers_feed_service,
    get_numbers_for_entity,
)
from core.numbers.insight_service import generate_numbers_insight


# ============================================================
# TABLES
# ============================================================

TABLE_NUMBERS = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS"
TABLE_NUMBERS_TYPES = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS_TYPE"


# ============================================================
# CREATE
# ============================================================

def create_number_service(data):
    return create_number(data)


# ============================================================
# LIST
# ============================================================

def list_numbers(limit: int = 100):

    return query_bq(f"""
        SELECT *
        FROM `{TABLE_NUMBERS}`
        ORDER BY CREATED_AT DESC
        LIMIT @limit
    """, {"limit": limit})


# ============================================================
# DELETE
# ============================================================

def delete_number(id_number: str):

    # relations
    query_bq(f"""
        DELETE FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS_COMPANY`
        WHERE ID_NUMBER = @id
    """, {"id": id_number})

    query_bq(f"""
        DELETE FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS_TOPIC`
        WHERE ID_NUMBER = @id
    """, {"id": id_number})

    query_bq(f"""
        DELETE FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS_SOLUTION`
        WHERE ID_NUMBER = @id
    """, {"id": id_number})

    # main
    query_bq(f"""
        DELETE FROM `{TABLE_NUMBERS}`
        WHERE ID_NUMBER = @id
    """, {"id": id_number})


# ============================================================
# TYPES
# ============================================================

def get_number_types():

    rows = query_bq(f"""
        SELECT ID_TYPE, TYPE
        FROM `{TABLE_NUMBERS_TYPES}`
        WHERE IS_ACTIVE = TRUE OR IS_ACTIVE IS NULL
        ORDER BY TYPE
    """)

    return [
        {
            "id": r["ID_TYPE"],
            "label": r["TYPE"],
        }
        for r in rows
    ]


# ============================================================
# COHERENCE
# ============================================================

def check_number_coherence_service(payload: dict):

    return check_number_coherence(
        value=payload.get("value"),
        id_number_type=payload.get("id_number_type"),
        zone=payload.get("zone"),
        period=payload.get("period"),
        company_id=payload.get("company_id"),
        topic_id=payload.get("topic_id"),
        solution_id=payload.get("solution_id"),
    )


# ============================================================
# SEARCH
# ============================================================

def search_numbers(
    id_number_type: Optional[str] = None,
    topic_id: Optional[str] = None,
    company_id: Optional[str] = None,
    solution_id: Optional[str] = None,
    limit: int = 200,
):

    return search_numbers_service(
        id_number_type=id_number_type,
        topic_id=topic_id,
        company_id=company_id,
        solution_id=solution_id,
        limit=limit,
    )


# ============================================================
# FEED
# ============================================================

def get_numbers_feed(
    limit: int = 50,
    query: Optional[str] = None,
    universe_id: Optional[str] = None,
):

    return get_numbers_feed_service(
        limit=limit,
        query=query,
        universe_id=universe_id,
    )


# ============================================================
# ENTITY
# ============================================================

def numbers_by_entity(
    entity_type: str,
    entity_id: str,
    limit: Optional[int] = None,
):

    return get_numbers_for_entity(
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit,
    )


# ============================================================
# INSIGHT
# ============================================================

def numbers_insight(ids: List[str]):

    return generate_numbers_insight(ids)
