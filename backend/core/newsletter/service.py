from typing import (
    Optional,
    List,
    Dict,
)

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
) -> Dict:

    news = _search_newsletter_items(
        topics=topics,
        companies=companies,
        news_types=news_types,
        limit=limit,
        cursor=cursor,
        news_kind="NEWS",
        period=period,
        date_from=date_from,
        date_to=date_to,
    )

    breves = _search_newsletter_items(
        topics=topics,
        companies=companies,
        news_types=news_types,
        limit=limit,
        cursor=cursor,
        news_kind="BRIEF",
        period=period,
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
