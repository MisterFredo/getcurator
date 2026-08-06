from typing import List, Dict, Optional

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq

from core.user.user_service import get_user_context


# ============================================================
# TABLES / VIEWS
# ============================================================

TABLE_CONTENT_ENRICHED = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_ENRICHED"
)

VIEW_STATS_TOPIC = (
    f"{BQ_PROJECT}.{BQ_DATASET}.V_CONTENT_STATS_TOPIC"
)

TABLE_TOPIC = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOPIC"
)

TABLE_COMPANY_UNIVERSE = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY_UNIVERSE"
)

TABLE_USER_UNIVERSE = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_UNIVERSE"
)


# ============================================================
# FEED
# ============================================================

def _get_topic_feed(
    topic_id: str,
    limit: int = 50,
    offset: int = 0,
    user_id: Optional[str] = None,
    universe_id: Optional[str] = None,
    lang: str = "fr",
) -> List[Dict]:

    user_filter = ""

    if user_id:

        user_filter = f"""
        AND EXISTS (
            SELECT 1
            FROM UNNEST(c.companies) comp

            JOIN `{TABLE_COMPANY_UNIVERSE}` cu
              ON cu.ID_COMPANY = comp.id_company

            JOIN `{TABLE_USER_UNIVERSE}` uu
              ON uu.ID_UNIVERSE = cu.ID_UNIVERSE

            WHERE uu.ID_USER = @user_id
        )
        """

    universe_filter = ""

    if universe_id:

        universe_filter = f"""
        AND EXISTS (
            SELECT 1
            FROM UNNEST(c.companies) comp

            JOIN `{TABLE_COMPANY_UNIVERSE}` cu
              ON cu.ID_COMPANY = comp.id_company

            WHERE cu.ID_UNIVERSE = @universe_id
        )
        """

    sql = f"""
    SELECT

        c.id_content AS id,

        c.title,
        c.title_en,

        c.excerpt,
        c.excerpt_en,

        c.published_at

    FROM `{TABLE_CONTENT_ENRICHED}` c

    WHERE EXISTS (

        SELECT 1

        FROM UNNEST(c.topics) t

        WHERE t.id_topic = @topic_id

    )

    {user_filter}

    {universe_filter}

    ORDER BY c.published_at DESC

    LIMIT @limit
    OFFSET @offset
    """

    rows = query_bq(
        sql,
        {
            "topic_id": topic_id,
            "limit": limit,
            "offset": offset,
            "user_id": user_id,
            "universe_id": universe_id,
        },
    )

    return [
        _map_content(
            row,
            lang,
        )
        for row in rows
    ]


# ============================================================
# PUBLIC VIEW
# ============================================================

def get_topic_view(
    topic_id: str,
    limit: int = 50,
    offset: int = 0,
    user_id: Optional[str] = None,
    universe_id: Optional[str] = None,
) -> Optional[Dict]:

    topic_rows = query_bq(
        f"""
        SELECT

            ID_TOPIC,
            LABEL,
            TOPIC_AXIS,
            DESCRIPTION

        FROM `{TABLE_TOPIC}`

        WHERE ID_TOPIC = @topic_id

        LIMIT 1
        """,
        {
            "topic_id": topic_id,
        },
    )

    if not topic_rows:
        return None

    topic = topic_rows[0]

    stats_rows = query_bq(
        f"""
        SELECT

            COALESCE(total, 0) AS NB_ANALYSES,

            COALESCE(last_30_days, 0) AS DELTA_30D

        FROM `{VIEW_STATS_TOPIC}`

        WHERE id_topic = @topic_id

        LIMIT 1
        """,
        {
            "topic_id": topic_id,
        },
    )

    stats = stats_rows[0] if stats_rows else {}

    context = (
        get_user_context(user_id)
        if user_id
        else None
    )

    lang = (
        context["lang"]
        if context
        else "fr"
    )

    items = _get_topic_feed(
        topic_id=topic_id,
        limit=limit,
        offset=offset,
        user_id=user_id,
        universe_id=universe_id,
        lang=lang,
    )

    return {

        "id_topic": topic_id,

        "label": topic.get("LABEL"),

        "topic_axis": topic.get("TOPIC_AXIS"),

        "description": topic.get("DESCRIPTION"),

        "nb_analyses": stats.get(
            "NB_ANALYSES",
            0,
        ),

        "delta_30d": stats.get(
            "DELTA_30D",
            0,
        ),

        "items": items,
    }


# ============================================================
# CONTENT MAPPER
# ============================================================

def _map_content(
    row: Dict,
    lang: str = "fr",
) -> Dict:

    def fmt(value):
        return value.isoformat() if value else None

    return {

        "id": row.get("id"),

        "title": (
            row.get("title_en")
            if lang == "en"
            else None
        ) or row.get("title"),

        "title_en": row.get("title_en"),

        "excerpt": (
            row.get("excerpt_en")
            if lang == "en"
            else None
        ) or row.get("excerpt"),

        "excerpt_en": row.get("excerpt_en"),

        "published_at": fmt(
            row.get("published_at")
        ),
    }
