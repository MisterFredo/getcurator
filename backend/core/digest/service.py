from typing import Optional, List, Dict, Any

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq


# ============================================================
# VIEWS
# ============================================================
VIEW_CONTENT_ENRICHED = f"{BQ_PROJECT}.{BQ_DATASET}.V_CONTENT_ENRICHED"
VIEW_NUMBERS_ENRICHED = f"{BQ_PROJECT}.{BQ_DATASET}.V_NUMBERS_ENRICHED"


# ============================================================
# PUBLIC API
# ============================================================

from typing import Optional, List, Dict, Any

# ============================================================
# MAIN
# ============================================================

def search_digest(
    topics: Optional[List[str]] = None,
    companies: Optional[List[str]] = None,
    news_types: Optional[List[str]] = None,
    limit: int = 20,
    cursor: Optional[str] = None,
    period: Optional[str] = "total",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    blocks_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:

    use_period = period
    if date_from or date_to:
        use_period = None

    # =========================================================
    # 🔥 BLOCK CONFIG (NEW)
    # =========================================================

    def get_block(name):
        if not blocks_config:
            return None
        return blocks_config.get(name, {})

    def resolve_limit(block):
        if not block:
            return limit
        return block.get("limit", limit)

    def resolve_topics(block):
        return block.get("topics") if block else topics

    def resolve_companies(block):
        return block.get("companies") if block else companies

    def resolve_types(block):
        return block.get("news_types") if block else news_types

    def resolve_period(block):
        if not block:
            return use_period
        return block.get("period", use_period)

    # =========================================================
    # ANALYSES
    # =========================================================

    analyses_block = get_block("analyses")

    analyses = []
    if not analyses_block or resolve_limit(analyses_block) > 0:
        analyses = _search_analyses_digest(
            topics=resolve_topics(analyses_block),
            companies=resolve_companies(analyses_block),
            limit=resolve_limit(analyses_block),
            cursor=cursor,
            period=resolve_period(analyses_block),
            date_from=date_from,
            date_to=date_to,
        )

    # =========================================================
    # NUMBERS (optionnel)
    # =========================================================

    numbers = _search_numbers_digest(
        topics=topics,
        companies=companies,
        limit=limit,
        period=use_period,
    )

    return {
        "news": news,
        "breves": breves,
        "analyses": analyses,
        "numbers": numbers,
    }

# ============================================================
# ANALYSES
# ============================================================

def _search_analyses_digest(
    topics,
    companies,
    limit,
    cursor,
    period,
    date_from=None,
    date_to=None,
):

    where_clauses = [
        "published_at IS NOT NULL",
    ]

    params = {"limit": limit}

    # -------------------------
    # FILTERS
    # -------------------------

    if topics:
        where_clauses.append("""
            EXISTS (
                SELECT 1
                FROM UNNEST(topics) t
                WHERE t.id_topic IN UNNEST(@topics)
            )
        """)
        params["topics"] = topics

    if companies:
        where_clauses.append("""
            EXISTS (
                SELECT 1
                FROM UNNEST(companies) c
                WHERE c.id_company IN UNNEST(@companies)
            )
        """)
        params["companies"] = companies

    if cursor:
        where_clauses.append("published_at < @cursor")
        params["cursor"] = cursor

    # -------------------------
    # DATE OVERRIDE
    # -------------------------

    if date_from:
        where_clauses.append("DATE(published_at) >= DATE(@date_from)")
        params["date_from"] = date_from

    if date_to:
        where_clauses.append("DATE(published_at) <= DATE(@date_to)")
        params["date_to"] = date_to

    # -------------------------
    # PERIOD
    # -------------------------

    if not date_from and not date_to:
        if period == "7d":
            where_clauses.append(
                "DATE(published_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)"
            )
        elif period == "30d":
            where_clauses.append(
                "DATE(published_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)"
            )

    # -------------------------
    # SQL
    # -------------------------

    sql = f"""
        SELECT
            id_content,
            title,
            excerpt,
            published_at,
            topics,
            companies
        FROM `{VIEW_CONTENT_ENRICHED}`
        WHERE {" AND ".join(where_clauses)}
        ORDER BY published_at DESC
        LIMIT @limit
    """

    rows = query_bq(sql, params)

    return [
        {
            "id": r["id_content"],
            "title": r["title"],
            "excerpt": r["excerpt"],
            "published_at": r["published_at"],
            "topics": r["topics"] or [],
            "companies": r["companies"] or [],
        }
        for r in rows
    ]

def _search_numbers_digest(
    topics,
    companies,
    limit,
    period,
    date_from=None,
    date_to=None,
):

    where_clauses = []
    params = {"limit": limit}

    # =========================================================
    # 🔥 FILTER TOPICS
    # =========================================================

    if topics:
        where_clauses.append("""
            EXISTS (
                SELECT 1
                FROM UNNEST(@topics) t
                WHERE ENTITY_TYPE = 'topic'
                AND ENTITY_ID = t
            )
        """)
        params["topics"] = topics

    # =========================================================
    # 🔥 FILTER COMPANIES
    # =========================================================

    if companies:
        where_clauses.append("""
            ENTITY_TYPE = 'company'
            AND ENTITY_ID IN UNNEST(@companies)
        """)
        params["companies"] = companies

    # =========================================================
    # 🔥 DATE OVERRIDE (PRIORITAIRE)
    # =========================================================

    if date_from:
        where_clauses.append("DATE(CREATED_AT) >= DATE(@date_from)")
        params["date_from"] = date_from

    if date_to:
        where_clauses.append("DATE(CREATED_AT) <= DATE(@date_to)")
        params["date_to"] = date_to

    # =========================================================
    # 🔥 PERIOD (fallback si pas de dates)
    # =========================================================

    if not date_from and not date_to:
        if period == "7d":
            where_clauses.append(
                "DATE(CREATED_AT) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)"
            )
        elif period == "30d":
            where_clauses.append(
                "DATE(CREATED_AT) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)"
            )

    # =========================================================
    # SQL
    # =========================================================

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    sql = f"""
        SELECT
            ID_NUMBER,
            ENTITY_TYPE,
            ENTITY_ID,
            ENTITY_LABEL,
            LABEL,
            VALUE,
            UNIT,
            SCALE,
            TYPE,
            CATEGORY,
            ZONE,
            PERIOD,
            CREATED_AT
        FROM `{VIEW_NUMBERS_ENRICHED}`
        {where_sql}
        ORDER BY CREATED_AT DESC
        LIMIT @limit
    """

    rows = query_bq(sql, params)

    return [
        {
            "id": r["ID_NUMBER"],
            "label": r["LABEL"],
            "value": r["VALUE"],
            "unit": r["UNIT"],
            "scale": r["SCALE"],
            "type": r["TYPE"],
            "category": r["CATEGORY"],
            "zone": r["ZONE"],
            "period": r["PERIOD"],
            "created_at": r["CREATED_AT"],
            "entity": {
                "type": r["ENTITY_TYPE"],
                "id": r["ENTITY_ID"],
                "label": r["ENTITY_LABEL"],
            },
        }
        for r in rows
    ]
