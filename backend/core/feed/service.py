from typing import List, Dict, Optional

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq

from core.user.user_service import get_user_context
from core.user.user_preferences_service import get_user_preferences_grouped


TABLE_NEWS = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NEWS"
TABLE_CONTENT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"

TABLE_NEWS_TOPIC = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NEWS_TOPIC"
TABLE_NEWS_SOLUTION = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NEWS_SOLUTION"

TABLE_CONTENT_TOPIC = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_TOPIC"
TABLE_CONTENT_SOLUTION = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_SOLUTION"
TABLE_CONTENT_COMPANY = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_COMPANY"

TABLE_TOPIC = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOPIC"
TABLE_COMPANY = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY"
TABLE_SOLUTION = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION"


# ============================================================
# SEARCH — MODE TEXTE (SEARCH INDEX)
# ============================================================

def search_text(
    query: str,
    limit: int = 20,
    offset: int = 0,
) -> List[Dict]:

    query = query.strip()

    sql = f"""
    SELECT
        n.ID_NEWS as id,
        'news' as type,
        n.TITLE,
        n.TITLE_EN,
        n.EXCERPT,
        n.EXCERPT_EN,
        n.PUBLISHED_AT
    FROM `{TABLE_NEWS}` n
    WHERE n.STATUS = 'PUBLISHED'
      AND SEARCH(n, @query)

    UNION ALL

    SELECT
        c.ID_CONTENT as id,
        'analysis' as type,
        c.TITLE,
        c.TITLE_EN,
        c.EXCERPT,
        c.EXCERPT_EN,
        c.PUBLISHED_AT
    FROM `{TABLE_CONTENT}` c
    WHERE c.STATUS = 'PUBLISHED'
      AND c.IS_ACTIVE = TRUE
      AND SEARCH(c, @query)

    ORDER BY PUBLISHED_AT DESC
    LIMIT @limit
    OFFSET @offset
    """

    return query_bq(sql, {
        "query": query,
        "limit": limit,
        "offset": offset,
    })


# ============================================================
# SEARCH — MODE FILTRES (SQL PUR)
# ============================================================

def search_filters(
    topic_ids: Optional[List[str]] = None,
    company_ids: Optional[List[str]] = None,
    solution_ids: Optional[List[str]] = None,
    news_types: Optional[List[str]] = None,
    limit: int = 20,
    offset: int = 0,
) -> List[Dict]:

    # 🔥 NORMALISATION SIMPLE ET SAFE
    def clean(v):
        if v is None:
            return None

        # 🔥 string → list (CRITIQUE)
        if isinstance(v, str):
            if v.strip() == "":
                return None
            return [v]

        # 🔥 list vide → None
        if isinstance(v, list):
            return v if len(v) > 0 else None

        return None

    topic_ids = clean(topic_ids)
    company_ids = clean(company_ids)
    solution_ids = clean(solution_ids)
    news_types = clean(news_types)

    sql = f"""
    SELECT
        n.ID_NEWS as id,
        'news' as type,
        n.TITLE,
        n.EXCERPT,
        n.PUBLISHED_AT
    FROM `{TABLE_NEWS}` n
    WHERE n.STATUS = 'PUBLISHED'

    AND (@news_types IS NULL OR n.NEWS_TYPE IN UNNEST(@news_types))
    AND (@company_ids IS NULL OR n.ID_COMPANY IN UNNEST(@company_ids))

    AND (
        @topic_ids IS NULL OR EXISTS (
            SELECT 1
            FROM `{TABLE_NEWS_TOPIC}` nt
            WHERE nt.ID_NEWS = n.ID_NEWS
              AND nt.ID_TOPIC IN UNNEST(@topic_ids)
        )
    )

    AND (
        @solution_ids IS NULL OR EXISTS (
            SELECT 1
            FROM `{TABLE_NEWS_SOLUTION}` ns
            WHERE ns.ID_NEWS = n.ID_NEWS
              AND ns.ID_SOLUTION IN UNNEST(@solution_ids)
        )
    )

    UNION ALL

    SELECT
        c.ID_CONTENT as id,
        'analysis' as type,
        c.TITLE,
        c.TITLE_EN,
        c.EXCERPT,
        c.EXCERPT_EN,
        c.PUBLISHED_AT
    FROM `{TABLE_CONTENT}` c
    WHERE c.STATUS = 'PUBLISHED'
      AND c.IS_ACTIVE = TRUE

    AND (
        @company_ids IS NULL OR EXISTS (
            SELECT 1
            FROM `{TABLE_CONTENT_COMPANY}` cc
            WHERE cc.ID_CONTENT = c.ID_CONTENT
              AND cc.ID_COMPANY IN UNNEST(@company_ids)
        )
    )

    AND (
        @topic_ids IS NULL OR EXISTS (
            SELECT 1
            FROM `{TABLE_CONTENT_TOPIC}` ct
            WHERE ct.ID_CONTENT = c.ID_CONTENT
              AND ct.ID_TOPIC IN UNNEST(@topic_ids)
        )
    )

    AND (
        @solution_ids IS NULL OR EXISTS (
            SELECT 1
            FROM `{TABLE_CONTENT_SOLUTION}` cs
            WHERE cs.ID_CONTENT = c.ID_CONTENT
              AND cs.ID_SOLUTION IN UNNEST(@solution_ids)
        )
    )

    ORDER BY PUBLISHED_AT DESC
    LIMIT @limit
    OFFSET @offset
    """

    return query_bq(sql, {
        "topic_ids": topic_ids,
        "company_ids": company_ids,
        "solution_ids": solution_ids,
        "news_types": news_types,
        "limit": limit,
        "offset": offset,
    })


# ============================================================
# META (ALIGNÉ FILTRES)
# ============================================================

def get_feed_meta() -> Dict:

    sql = f"""
    SELECT
        'topic' AS type,
        t.ID_TOPIC AS id,
        t.LABEL AS label,
        COUNT(DISTINCT nt.ID_NEWS) + COUNT(DISTINCT ct.ID_CONTENT) AS count
    FROM `{TABLE_TOPIC}` t
    LEFT JOIN `{TABLE_NEWS_TOPIC}` nt ON nt.ID_TOPIC = t.ID_TOPIC
    LEFT JOIN `{TABLE_CONTENT_TOPIC}` ct ON ct.ID_TOPIC = t.ID_TOPIC
    GROUP BY t.ID_TOPIC, t.LABEL

    UNION ALL

    SELECT
        'company' AS type,
        c.ID_COMPANY AS id,
        c.NAME AS label,
        COUNT(DISTINCT n.ID_NEWS) + COUNT(DISTINCT cc.ID_CONTENT) AS count
    FROM `{TABLE_COMPANY}` c
    LEFT JOIN `{TABLE_NEWS}` n
        ON n.ID_COMPANY = c.ID_COMPANY AND n.STATUS = 'PUBLISHED'
    LEFT JOIN `{TABLE_CONTENT_COMPANY}` cc
        ON cc.ID_COMPANY = c.ID_COMPANY
    GROUP BY c.ID_COMPANY, c.NAME

    UNION ALL

    SELECT
        'solution' AS type,
        s.ID_SOLUTION AS id,
        s.NAME AS label,
        COUNT(DISTINCT ns.ID_NEWS) + COUNT(DISTINCT cs.ID_CONTENT) AS count
    FROM `{TABLE_SOLUTION}` s
    LEFT JOIN `{TABLE_NEWS_SOLUTION}` ns ON ns.ID_SOLUTION = s.ID_SOLUTION
    LEFT JOIN `{TABLE_CONTENT_SOLUTION}` cs ON cs.ID_SOLUTION = s.ID_SOLUTION
    GROUP BY s.ID_SOLUTION, s.NAME

    UNION ALL

    SELECT
        'news_type' AS type,
        n.NEWS_TYPE AS id,
        n.NEWS_TYPE AS label,
        COUNT(*) AS count
    FROM `{TABLE_NEWS}` n
    WHERE n.STATUS = 'PUBLISHED'
      AND n.NEWS_TYPE IS NOT NULL
    GROUP BY n.NEWS_TYPE

    ORDER BY type, count DESC
    """

    rows = query_bq(sql)

    result = {
        "topics": [],
        "companies": [],
        "solutions": [],
        "news_types": []
    }

    for r in rows:
        if not r.get("id") or not r.get("label"):
            continue

        item = {
            "id": r["id"],
            "label": r["label"],
            "count": r.get("count", 0),
        }

        if r["type"] == "topic":
            result["topics"].append(item)

        elif r["type"] == "company":
            result["companies"].append(item)

        elif r["type"] == "solution":
            result["solutions"].append(item)

        elif r["type"] == "news_type":
            result["news_types"].append(item)

        return result

def get_feed_for_user(
    user_id: str,
    topic_ids=None,
    company_ids=None,
    solution_ids=None,
    limit: int = 20,
    offset: int = 0,
):

    # --------------------------------------------------------
    # USER CONTEXT
    # --------------------------------------------------------

    context = get_user_context(user_id)
    prefs = get_user_preferences_grouped(user_id)

    lang = context["lang"]

    # --------------------------------------------------------
    # MERGE FILTERS
    # --------------------------------------------------------

    final_topic_ids = topic_ids or prefs["TOPIC"]
    final_company_ids = company_ids or prefs["COMPANY"]
    final_solution_ids = solution_ids or prefs["SOLUTION"]

    # --------------------------------------------------------
    # FETCH DATA (EXISTING ENGINE)
    # --------------------------------------------------------

    items = search_filters(
        topic_ids=final_topic_ids,
        company_ids=final_company_ids,
        solution_ids=final_solution_ids,
        limit=limit,
        offset=offset,
    )

    # --------------------------------------------------------
    # TRANSLATION
    # --------------------------------------------------------

    if lang != "fr":
        items = translate_feed_items(items, lang)

    return items
