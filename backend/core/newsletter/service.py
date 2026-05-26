from typing import Optional, List, Dict, Any

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
)

# ============================================================
# VIEW
# ============================================================

VIEW_NEWS_ENRICHED = (
    f"{BQ_PROJECT}.{BQ_DATASET}.V_NEWS_ENRICHED"
)

# ============================================================
# MAIN
# ============================================================

def search_newsletter_content(
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
    # BLOCK CONFIG
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
    # NEWS
    # =========================================================

    news_block = get_block("news")

    news = []

    if not news_block or resolve_limit(news_block) > 0:

        news = _search_newsletter_items(
            topics=resolve_topics(news_block),
            companies=resolve_companies(news_block),
            news_types=resolve_types(news_block),
            limit=resolve_limit(news_block),
            cursor=cursor,
            news_kind="NEWS",
            period=resolve_period(news_block),
            date_from=date_from,
            date_to=date_to,
        )

    # =========================================================
    # BRÈVES
    # =========================================================

    breves_block = get_block("breves")

    breves = []

    if not breves_block or resolve_limit(breves_block) > 0:

        breves = _search_newsletter_items(
            topics=resolve_topics(breves_block),
            companies=resolve_companies(breves_block),
            news_types=resolve_types(breves_block),
            limit=resolve_limit(breves_block),
            cursor=cursor,
            news_kind="BRIEF",
            period=resolve_period(breves_block),
            date_from=date_from,
            date_to=date_to,
        )

    return {
        "news": news,
        "breves": breves,
    }

# ============================================================
# NEWS / BRÈVES
# ============================================================

def _search_newsletter_items(
    topics,
    companies,
    news_types,
    limit,
    cursor,
    news_kind,
    period,
    date_from=None,
    date_to=None,
):

    where_clauses = [
        "status = 'PUBLISHED'",
        "published_at IS NOT NULL",
        f"news_kind = '{news_kind}'",
    ]

    params = {
        "limit": limit,
    }

    # =========================================================
    # FILTER TOPICS
    # =========================================================

    if topics:

        where_clauses.append("""
            EXISTS (
                SELECT 1
                FROM UNNEST(topics) t
                WHERE t.id_topic IN UNNEST(@topics)
            )
        """)

        params["topics"] = topics

    # =========================================================
    # FILTER COMPANIES
    # =========================================================

    if companies:

        where_clauses.append("""
            id_company IN UNNEST(@companies)
        """)

        params["companies"] = companies

    # =========================================================
    # FILTER NEWS TYPES
    # =========================================================

    if news_types:

        where_clauses.append("""
            news_type IN UNNEST(@news_types)
        """)

        params["news_types"] = news_types

    # =========================================================
    # CURSOR
    # =========================================================

    if cursor:

        where_clauses.append("""
            published_at < @cursor
        """)

        params["cursor"] = cursor

    # =========================================================
    # DATE OVERRIDE
    # =========================================================

    if date_from:

        where_clauses.append("""
            DATE(published_at) >= DATE(@date_from)
        """)

        params["date_from"] = date_from

    if date_to:

        where_clauses.append("""
            DATE(published_at) <= DATE(@date_to)
        """)

        params["date_to"] = date_to

    # =========================================================
    # PERIOD
    # =========================================================

    if not date_from and not date_to:

        if period == "7d":

            where_clauses.append("""
                DATE(published_at)
                >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
            """)

        elif period == "30d":

            where_clauses.append("""
                DATE(published_at)
                >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
            """)

    # =========================================================
    # SQL
    # =========================================================

    sql = f"""
        SELECT
            id_news,
            title,
            excerpt,
            published_at,
            news_type,
            news_kind,
            visual_rect_id,
            id_company,
            company_name,
            is_partner,
            topics
        FROM `{VIEW_NEWS_ENRICHED}`
        WHERE {" AND ".join(where_clauses)}
        ORDER BY published_at DESC
        LIMIT @limit
    """

    rows = query_bq(
        sql,
        params,
    )

    # =========================================================
    # FORMAT
    # =========================================================

    return [
        {
            "id": r["id_news"],
            "title": r["title"],
            "excerpt": r["excerpt"],
            "published_at": r["published_at"],
            "news_type": r["news_type"],
            "news_kind": r["news_kind"],
            "visual_rect_id": r["visual_rect_id"],

            "company": {
                "id_company": r["id_company"],
                "name": r["company_name"],
                "is_partner": bool(r["is_partner"]),
            },

            "topics": r["topics"] or [],
        }
        for r in rows
    ]
