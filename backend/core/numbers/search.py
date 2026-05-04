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
# SEARCH (ADMIN / EXPLORATION)
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

    sql = f"""
    SELECT
        n.ID_NUMBER AS id_number,
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
# FEED (CURATOR)
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
    SELECT
        n.ID_NUMBER,
        n.LABEL,
        n.VALUE,
        n.UNIT,
        n.SCALE,
        n.TYPE,
        n.CATEGORY,
        n.ZONE,
        n.PERIOD,
        n.ENTITIES,
        n.CREATED_AT,

        -- 🔥 AJOUT CONTEXT
        ANY_VALUE(b.ID_CONTENT) AS context_id,
        ANY_VALUE(c.TITLE) AS context_title

    FROM `{VIEW_NUMBERS_CARDS}` n

    -- 🔥 JOIN BACKLOG (liaison number → content)
    LEFT JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS_BACKLOG` b
      ON b.LABEL = n.LABEL

    -- 🔥 JOIN CONTENT
    LEFT JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT` c
      ON c.ID_CONTENT = b.ID_CONTENT

    WHERE {where_sql}

    GROUP BY
        n.ID_NUMBER,
        n.LABEL,
        n.VALUE,
        n.UNIT,
        n.SCALE,
        n.TYPE,
        n.CATEGORY,
        n.ZONE,
        n.PERIOD,
        n.ENTITIES,
        n.CREATED_AT

    ORDER BY n.CREATED_AT DESC
    LIMIT @limit
    """

    return query_bq(sql, params)


# ============================================================
# ADMIN (🔥 CONTROL PANEL)
# ============================================================

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
        nt.CATEGORY,
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
# BY ENTITY (CURATOR DRAWER)
# ============================================================

def get_numbers_for_entity(
    entity_type: str,
    entity_id: str,
    limit: Optional[int] = None
) -> List[Dict]:

    if entity_type == "company":
        table_rel = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS_COMPANY"
        field = "ID_COMPANY"

    elif entity_type == "solution":
        table_rel = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS_SOLUTION"
        field = "ID_SOLUTION"

    elif entity_type == "topic":
        table_rel = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS_TOPIC"
        field = "ID_TOPIC"

    else:
        raise ValueError("Invalid entity_type")

    sql = f"""
        SELECT
            n.ID_NUMBER,
            n.LABEL,
            n.VALUE,
            n.UNIT,
            n.SCALE,

            t.TYPE,
            t.CATEGORY,

            n.ZONE,
            n.PERIOD,

            n.CREATED_AT

        FROM `{table_rel}` rel

        JOIN `{TABLE_NUMBERS}` n
          ON n.ID_NUMBER = rel.ID_NUMBER

        LEFT JOIN `{TABLE_NUMBERS_TYPES}` t
          ON t.ID_TYPE = n.ID_NUMBER_TYPE

        WHERE rel.{field} = @entity_id
        AND (t.IS_ACTIVE = TRUE OR t.IS_ACTIVE IS NULL)
        AND n.VALUE IS NOT NULL

        ORDER BY n.CREATED_AT DESC
    """

    rows = query_bq(sql, {
        "entity_id": entity_id
    })

    if limit:
        rows = rows[:limit]

    return rows
