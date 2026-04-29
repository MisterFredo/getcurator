from typing import Optional, List, Dict

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq

TABLE_NUMBERS = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS"
TABLE_NUMBERS_TYPES = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS_TYPE"
TABLE_NUMBERS_COMPANY = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS_COMPANY"
TABLE_NUMBERS_TOPIC = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS_TOPIC"
TABLE_NUMBERS_SOLUTION = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS_SOLUTION"

VIEW_NUMBERS = f"{BQ_PROJECT}.{BQ_DATASET}.V_NUMBERS_ENRICHED"
VIEW_NUMBERS_CARDS = f"{BQ_PROJECT}.{BQ_DATASET}.V_NUMBERS_CARDS"


# ============================================================
# SEARCH
# ============================================================

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

    if id_number_type:
        conditions.append("n.ID_NUMBER_TYPE = @id_number_type")
        params["id_number_type"] = id_number_type

    if company_id:
        joins.append("""
            JOIN `{TABLE_NUMBERS_COMPANY}` nc_filter
              ON n.ID_NUMBER = nc_filter.ID_NUMBER
        """)
        conditions.append("nc_filter.ID_COMPANY = @company_id")
        params["company_id"] = company_id

    if topic_id:
        joins.append("""
            JOIN `{TABLE_NUMBERS_TOPIC}` nt_filter
              ON n.ID_NUMBER = nt_filter.ID_NUMBER
        """)
        conditions.append("nt_filter.ID_TOPIC = @topic_id")
        params["topic_id"] = topic_id

    if solution_id:
        joins.append("""
            JOIN `{TABLE_NUMBERS_SOLUTION}` ns_filter
              ON n.ID_NUMBER = ns_filter.ID_NUMBER
        """)
        conditions.append("ns_filter.ID_SOLUTION = @solution_id")
        params["solution_id"] = solution_id

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

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
        n.CREATED_AT AS created_at

    FROM `{TABLE_NUMBERS}` n

    LEFT JOIN `{TABLE_NUMBERS_TYPES}` nt
      ON n.ID_NUMBER_TYPE = nt.ID_TYPE

    {" ".join(joins)}

    {where_clause}

    ORDER BY n.CREATED_AT DESC
    LIMIT @limit
    """

    return query_bq(sql, params)


# ============================================================
# FEED
# ============================================================

def get_numbers_feed_service(
    limit: int = 50,
    query: Optional[str] = None,
    universe_id: Optional[str] = None,
):

    where_clauses = ["TRUE"]
    params = {"limit": limit}

    if query:
        where_clauses.append("LOWER(n.LABEL) LIKE LOWER(@query)")
        params["query"] = f"%{query}%"

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

    sql = f"""
    SELECT *
    FROM `{VIEW_NUMBERS_CARDS}` n
    WHERE {where_sql}
    ORDER BY n.CREATED_AT DESC
    LIMIT @limit
    """

    return query_bq(sql, params)

def get_numbers_admin_service(
    limit: int = 200,
    offset: int = 0,
    query: Optional[str] = None,
    type_id: Optional[str] = None,
    source_id: Optional[str] = None,
):
    conditions = []
    params = {
        "limit": limit,
        "offset": offset,
    }

    if query:
        conditions.append("LOWER(n.LABEL) LIKE LOWER(@query)")
        params["query"] = f"%{query}%"

    if type_id:
        conditions.append("n.ID_NUMBER_TYPE = @type_id")
        params["type_id"] = type_id

    if source_id:
        conditions.append("n.ID_SOURCE = @source_id")
        params["source_id"] = source_id

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    sql = f"""
    SELECT
        n.ID_NUMBER,
        n.LABEL,
        n.VALUE,
        n.UNIT,
        n.SCALE,
        nt.TYPE,
        n.ZONE,
        n.PERIOD,
        n.ID_SOURCE,
        n.CREATED_AT

    FROM `{TABLE_NUMBERS}` n

    LEFT JOIN `{TABLE_NUMBERS_TYPES}` nt
      ON n.ID_NUMBER_TYPE = nt.ID_TYPE

    {where_clause}

    ORDER BY n.CREATED_AT DESC
    LIMIT @limit
    OFFSET @offset
    """

    return query_bq(sql, params)


# ============================================================
# BY ENTITY
# ============================================================

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
            PERIOD
        FROM `{VIEW_NUMBERS}`
        WHERE ENTITY_TYPE = @entity_type
          AND ENTITY_ID = @entity_id
        ORDER BY PERIOD DESC
    """

    rows = query_bq(sql, {
        "entity_type": entity_type,
        "entity_id": entity_id
    })

    if limit:
        rows = rows[:limit]

    return rows
