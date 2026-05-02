# ============================================================
# IMPORTS
# ============================================================

from typing import List, Dict, Optional

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq

from core.numbers.insight_service import build_numbers_prompt
from utils.llm import run_llm


# ============================================================
# TABLES
# ============================================================

TABLE_BACKLOG = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS_BACKLOG"
TABLE_CONTENT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"


# ============================================================
# FEED (CURATOR V1)
# ============================================================

def get_backlog_feed(limit: int = 50) -> List[Dict]:

    rows = query_bq(f"""
        SELECT
            b.ID_BACKLOG,
            b.ID_CONTENT,
            c.TITLE AS context_title,

            b.LABEL,
            SAFE_CAST(b.VALUE AS FLOAT64) AS VALUE,
            b.UNIT,

            b.MARKET AS zone,
            b.PERIOD,

            b.CREATED_AT

        FROM `{TABLE_BACKLOG}` b

        LEFT JOIN `{TABLE_CONTENT}` c
          ON b.ID_CONTENT = c.ID_CONTENT

        WHERE b.DECISION IS NULL OR b.DECISION != 'IGNORE'

        ORDER BY b.CREATED_AT DESC
        LIMIT @limit
    """, {"limit": limit})

    return [
        {
            "id": r["ID_BACKLOG"],
            "label": r.get("LABEL"),
            "value": r.get("VALUE"),
            "unit": r.get("UNIT"),

            "zone": r.get("zone"),
            "period": r.get("PERIOD"),

            "context_title": r.get("context_title"),
            "source_type": "content",

            "created_at": r.get("CREATED_AT"),
        }
        for r in rows
    ]


# ============================================================
# ADMIN (GLOBAL PANEL)
# ============================================================

def get_backlog_admin(
    limit: int = 200,
    offset: int = 0,
    query: Optional[str] = None,
    decision: Optional[str] = None,
) -> List[Dict]:

    conditions = ["TRUE"]
    params = {
        "limit": limit,
        "offset": offset,
    }

    # 🔍 SEARCH (label + actor)
    if query:
        conditions.append("""
            (
                LOWER(b.LABEL) LIKE LOWER(@query)
                OR LOWER(b.ACTOR) LIKE LOWER(@query)
            )
        """)
        params["query"] = f"%{query}%"

    # 🔥 DECISION FILTER
    if decision == "NULL":
        conditions.append("b.DECISION IS NULL")

    elif decision:
        conditions.append("b.DECISION = @decision")
        params["decision"] = decision

    # 👉 si decision == "" → ALL → pas de filtre

    where_clause = " AND ".join(conditions)

    rows = query_bq(f"""
        SELECT
            b.ID_BACKLOG,
            b.ID_CONTENT,
            c.TITLE AS context_title,

            b.RAW_LINE,
            b.LABEL,
            SAFE_CAST(b.VALUE AS FLOAT64) AS VALUE,
            b.UNIT,

            b.ACTOR,
            b.MARKET,
            b.PERIOD,

            b.DECISION,
            b.CONFIDENCE,
            b.CONTEXT,

            b.CREATED_AT

        FROM `{TABLE_BACKLOG}` b

        LEFT JOIN `{TABLE_CONTENT}` c
          ON b.ID_CONTENT = c.ID_CONTENT

        WHERE {where_clause}

        ORDER BY b.CREATED_AT DESC

        LIMIT @limit
        OFFSET @offset
    """, params)

    return rows

# ============================================================
# UPDATE DECISION (ADMIN ACTION)
# ============================================================

def update_backlog_decision(id_backlog: str, decision: Optional[str]):

    query_bq(f"""
        UPDATE `{TABLE_BACKLOG}`
        SET DECISION = @decision
        WHERE ID_BACKLOG = @id
    """, {
        "id": id_backlog,
        "decision": decision,
    })


# ============================================================
# FETCH BY IDS (FOR INSIGHT)
# ============================================================

def get_backlog_numbers_by_ids(ids: List[str]) -> List[Dict]:

    if isinstance(ids, str):
        ids = [ids]

    if not ids:
        return []

    rows = query_bq(f"""
        SELECT
            b.ID_BACKLOG,
            c.TITLE AS context_title,

            b.LABEL,
            SAFE_CAST(b.VALUE AS FLOAT64) AS VALUE,
            b.UNIT,

            b.ACTOR,
            b.MARKET,
            b.PERIOD

        FROM `{TABLE_BACKLOG}` b

        LEFT JOIN `{TABLE_CONTENT}` c
          ON b.ID_CONTENT = c.ID_CONTENT

        WHERE b.ID_BACKLOG IN UNNEST(@ids)
    """, {"ids": ids})

    return [
        {
            "label": r.get("LABEL"),
            "value": r.get("VALUE"),
            "unit": r.get("UNIT"),
            "scale": None,

            "type": None,
            "category": None,

            "zone": r.get("MARKET"),
            "period": r.get("PERIOD"),

            "entity_label": r.get("ACTOR"),
        }
        for r in rows
    ]


# ============================================================
# INSIGHT (V1)
# ============================================================

def generate_backlog_insight(ids: List[str]) -> str:

    numbers = get_backlog_numbers_by_ids(ids)

    if not numbers:
        return ""

    prompt = build_numbers_prompt(numbers)

    result = run_llm(
        prompt=prompt,
        temperature=0.2,
    )

    return result or ""
