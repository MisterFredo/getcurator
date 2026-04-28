import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional

from google.cloud import bigquery

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq, get_bigquery_client


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
# MATCH EXISTING NUMBERS
# ============================================================

def find_existing_numbers(
    id_number_type: str,
    zone: str,
    period: str,
    company_ids: Optional[List[str]] = None,
    topic_ids: Optional[List[str]] = None,
    solution_ids: Optional[List[str]] = None,
) -> List[Dict]:

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

    rows = query_bq(f"""
        SELECT
            n.ID_NUMBER,
            n.LABEL,
            n.VALUE,
            n.SCALE,
            n.UNIT
        FROM `{TABLE_NUMBERS}` n
        {join}
        WHERE {condition}
        AND n.ID_NUMBER_TYPE = @type_id
        AND n.ZONE = @zone
        AND n.PERIOD = @period
        LIMIT 20
    """, {
        "entity_ids": entity_ids,
        "type_id": id_number_type,
        "zone": zone,
        "period": period,
    })

    return rows


# ============================================================
# PARSE CHIFFRES (FROM CONTENT)
# ============================================================

def parse_chiffres(chiffres: List[str]) -> List[Dict]:

    results = []

    for line in chiffres:

        if not line or "|" not in line:
            continue

        parts = [p.strip() for p in line.split("|")]

        if len(parts) != 6:
            continue

        label, value, unit_raw, actor, market, period = parts

        try:
            value = float(value)
        except:
            continue

        unit, scale = _extract_unit_scale(unit_raw)

        results.append({
            "label": label,
            "value": value,
            "unit": unit,
            "scale": scale,
            "actor": actor,
            "zone": market,
            "period": period,
        })

    return results


# ============================================================
# GET NUMBERS FROM CONTENT
# ============================================================

def get_numbers_from_content(id_content: str):

    TABLE_CONTENT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"

    rows = query_bq(f"""
        SELECT CHIFFRES
        FROM `{TABLE_CONTENT}`
        WHERE ID_CONTENT = @id_content
        LIMIT 1
    """, {
        "id_content": id_content
    })

    if not rows:
        return []

    chiffres = rows[0].get("CHIFFRES") or []

    return parse_chiffres(chiffres)


# ============================================================
# BASIC QUALITY CHECK
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
# COHERENCE CHECK
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


# ============================================================
# CREATE NUMBER
# ============================================================

def create_number(data) -> Dict:

    # 🔥 support Pydantic model + dict
    if hasattr(data, "dict"):
        data = data.dict()

    payload = normalize_number_payload(data)

    quality = check_basic_quality(
        value=payload["value"],
        id_number_type=payload["id_number_type"],
        zone=payload["zone"],
        period=payload["period"],
        company_ids=payload["company_ids"],
    )

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
        job_config=bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND"
        ),
    ).result()

    _insert_relations(
        id_number,
        payload.get("company_ids"),
        payload.get("topic_ids"),
        payload.get("solution_ids")
    )

    return {
        "id_number": id_number,
        "quality": quality
    }


# ============================================================
# RELATIONS
# ============================================================

def _insert_relations(id_number, company_ids, topic_ids, solution_ids):

    client = get_bigquery_client()

    if company_ids:
        rows = [{
            "ID_NUMBER": id_number,
            "ID_COMPANY": cid,
            "CREATED_AT": _now(),
        } for cid in company_ids]
        client.load_table_from_json(rows, TABLE_NUMBERS_COMPANY).result()

    if topic_ids:
        rows = [{
            "ID_NUMBER": id_number,
            "ID_TOPIC": tid,
            "CREATED_AT": _now(),
        } for tid in topic_ids]
        client.load_table_from_json(rows, TABLE_NUMBERS_TOPIC).result()

    if solution_ids:
        rows = [{
            "ID_NUMBER": id_number,
            "ID_SOLUTION": sid,
            "CREATED_AT": _now(),
        } for sid in solution_ids]
        client.load_table_from_json(rows, TABLE_NUMBERS_SOLUTION).result()


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
# RAW NUMBERS
# ============================================================

def get_raw_numbers(limit: int = 200):

    TABLE_CONTENT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"

    rows = query_bq(f"""
        SELECT ID_CONTENT, CHIFFRES
        FROM `{TABLE_CONTENT}`
        WHERE CHIFFRES IS NOT NULL
        LIMIT @limit
    """, {
        "limit": limit
    })

    results = []

    for r in rows:

        chiffres = r.get("CHIFFRES") or []

        if isinstance(chiffres, str):
            chiffres = chiffres.split("\n")

        for line in chiffres:

            parts = [p.strip() for p in line.split("|")]

            if len(parts) != 6:
                continue

            label, value, unit_raw, actor, market, period = parts

            try:
                value = float(value)
            except:
                continue

            unit, scale = _extract_unit_scale(unit_raw)

            results.append({
                "id_content": r["ID_CONTENT"],
                "label": label,
                "value": value,
                "unit": unit,
                "scale": scale,
                "actor": actor,
                "market": market,
                "period": period,
            })

    return results


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

def get_numbers_for_entity(
    entity_type: str,
    entity_id: str,
    limit: Optional[int] = None
) -> List[Dict]:

    sql = f"""
        SELECT
            ID_NUMBER,
            LABEL,
            VALUE,
            UNIT,
            SCALE,
            TYPE,
            CATEGORY,
            ZONE,
            PERIOD,
            CREATED_AT
        FROM `{VIEW_NUMBERS}`
        WHERE ENTITY_TYPE = @entity_type
          AND ENTITY_ID = @entity_id
        ORDER BY
            CATEGORY,
            TYPE,
            PERIOD DESC
    """

    rows = query_bq(sql, {
        "entity_type": entity_type,
        "entity_id": entity_id
    })

    # ============================================================
    # LIMIT (preview)
    # ============================================================

    if limit is not None:
        rows = rows[:limit]

    # ============================================================
    # GROUPING
    # ============================================================

    grouped = {}

    for r in rows:
        category = r.get("CATEGORY") or "OTHER"
        type_ = r.get("TYPE") or "UNKNOWN"

        if category not in grouped:
            grouped[category] = {}

        if type_ not in grouped[category]:
            grouped[category][type_] = []

        grouped[category][type_].append({
            "id_number": r.get("ID_NUMBER"),
            "label": r.get("LABEL"),
            "value": r.get("VALUE"),
            "unit": r.get("UNIT"),
            "scale": r.get("SCALE"),
            "zone": r.get("ZONE"),
            "period": r.get("PERIOD"),
        })

    # ============================================================
    # FORMAT FINAL
    # ============================================================

    result = []

    # tri des catégories
    sorted_categories = sorted(
        grouped.keys(),
        key=lambda c: CATEGORY_ORDER.index(c)
        if c in CATEGORY_ORDER else 999
    )

    for category in sorted_categories:
        types = grouped[category]

        type_list = []

        for type_ in sorted(types.keys()):
            type_list.append({
                "type": type_,
                "numbers": types[type_]
            })

        result.append({
            "category": category,
            "types": type_list
        })

    return result

def get_numbers_feed_service(
    limit: int = 50,
    query: Optional[str] = None,
    universe_id: Optional[str] = None,
):

    where_clauses = ["TRUE"]
    params = {"limit": limit}

    # ============================================================
    # 🔎 QUERY
    # ============================================================

    if query:
        where_clauses.append("LOWER(n.LABEL) LIKE LOWER(@query)")
        params["query"] = f"%{query}%"

    # ============================================================
    # 🌍 UNIVERSE FILTER
    # ============================================================

    if universe_id:
        where_clauses.append(f"""
        EXISTS (
            SELECT 1
            FROM UNNEST(n.ENTITIES) e2

            LEFT JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION` sc2
              ON e2.ENTITY_TYPE = 'solution'
             AND sc2.ID_SOLUTION = e2.ENTITY_ID

            JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY_UNIVERSE` cu2
              ON (
                (e2.ENTITY_TYPE = 'company' AND cu2.ID_COMPANY = e2.ENTITY_ID)
                OR
                (e2.ENTITY_TYPE = 'solution' AND cu2.ID_COMPANY = sc2.ID_COMPANY)
              )

            WHERE cu2.ID_UNIVERSE = @universe_id
        )
        """)
        params["universe_id"] = universe_id

    where_sql = " AND ".join(where_clauses)

    # ============================================================
    # QUERY
    # ============================================================

    sql = f"""
    WITH solution_company AS (
        SELECT ID_SOLUTION, ID_COMPANY
        FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION`
    )

    SELECT
        n.*,
        ARRAY_AGG(DISTINCT cu.ID_UNIVERSE IGNORE NULLS) AS universes

    FROM `{VIEW_NUMBERS_CARDS}` n

    LEFT JOIN UNNEST(n.ENTITIES) e

    LEFT JOIN solution_company sc
      ON e.ENTITY_TYPE = 'solution'
     AND sc.ID_SOLUTION = e.ENTITY_ID

    LEFT JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY_UNIVERSE` cu
      ON (
        (e.ENTITY_TYPE = 'company' AND cu.ID_COMPANY = e.ENTITY_ID)
        OR
        (e.ENTITY_TYPE = 'solution' AND cu.ID_COMPANY = sc.ID_COMPANY)
      )

    WHERE {where_sql}

    GROUP BY
        n.ID_NUMBER,
        n.LABEL,
        n.VALUE,
        n.UNIT,
        n.SCALE,
        n.ZONE,
        n.PERIOD,
        n.CREATED_AT,
        n.TYPE,
        n.CATEGORY,
        n.ENTITIES

    ORDER BY n.CREATED_AT DESC
    LIMIT @limit
    """

    return query_bq(sql, params)

def search_numbers_service(
    id_number_type: Optional[str] = None,
    topic_id: Optional[str] = None,
    company_id: Optional[str] = None,
    solution_id: Optional[str] = None,
    limit: int = 200,
):

    joins = []
    conditions = []
    params = {"limit": limit}

    # ============================================================
    # FILTERS
    # ============================================================

    if id_number_type:
        conditions.append("n.ID_NUMBER_TYPE = @id_number_type")
        params["id_number_type"] = id_number_type

    if company_id:
        joins.append(f"""
            JOIN `{TABLE_NUMBERS_COMPANY}` nc_filter
              ON n.ID_NUMBER = nc_filter.ID_NUMBER
        """)
        conditions.append("nc_filter.ID_COMPANY = @company_id")
        params["company_id"] = company_id

    if topic_id:
        joins.append(f"""
            JOIN `{TABLE_NUMBERS_TOPIC}` nt_filter
              ON n.ID_NUMBER = nt_filter.ID_NUMBER
        """)
        conditions.append("nt_filter.ID_TOPIC = @topic_id")
        params["topic_id"] = topic_id

    if solution_id:
        joins.append(f"""
            JOIN `{TABLE_NUMBERS_SOLUTION}` ns_filter
              ON n.ID_NUMBER = ns_filter.ID_NUMBER
        """)
        conditions.append("ns_filter.ID_SOLUTION = @solution_id")
        params["solution_id"] = solution_id

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    # ============================================================
    # QUERY
    # ============================================================

    sql = f"""
    SELECT
        n.ID_NUMBER AS id,
        n.LABEL AS label,
        n.VALUE AS value,
        n.UNIT AS unit,
        n.SCALE AS scale,
        nt.TYPE AS type,
        n.ZONE AS zone,
        n.PERIOD AS period,
        n.CREATED_AT AS created_at,

        ARRAY_AGG(DISTINCT t.LABEL IGNORE NULLS) AS topics,
        ARRAY_AGG(DISTINCT c.NAME IGNORE NULLS) AS companies,
        ARRAY_AGG(DISTINCT s.NAME IGNORE NULLS) AS solutions

    FROM `{TABLE_NUMBERS}` n

    LEFT JOIN `{TABLE_NUMBERS_TYPES}` nt
      ON n.ID_NUMBER_TYPE = nt.ID_TYPE

    LEFT JOIN `{TABLE_NUMBERS_TOPIC}` nt_rel
      ON n.ID_NUMBER = nt_rel.ID_NUMBER
    LEFT JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOPIC` t
      ON nt_rel.ID_TOPIC = t.ID_TOPIC

    LEFT JOIN `{TABLE_NUMBERS_COMPANY}` nc_rel
      ON n.ID_NUMBER = nc_rel.ID_NUMBER
    LEFT JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY` c
      ON nc_rel.ID_COMPANY = c.ID_COMPANY

    LEFT JOIN `{TABLE_NUMBERS_SOLUTION}` ns_rel
      ON n.ID_NUMBER = ns_rel.ID_NUMBER
    LEFT JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION` s
      ON ns_rel.ID_SOLUTION = s.ID_SOLUTION

    {" ".join(joins)}

    {where_clause}

    GROUP BY
        n.ID_NUMBER,
        n.LABEL,
        n.VALUE,
        n.UNIT,
        n.SCALE,
        nt.TYPE,
        n.ZONE,
        n.PERIOD,
        n.CREATED_AT

    ORDER BY n.CREATED_AT DESC
    LIMIT @limit
    """

    return query_bq(sql, params)
