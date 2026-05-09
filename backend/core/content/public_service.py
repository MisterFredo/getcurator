from typing import List, Dict, Optional

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq


# ============================================================
# TABLES
# ============================================================

TABLE_CONTENT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"

TABLE_CONTENT_ENRICHED = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_ENRICHED"
)

TABLE_CONTENT_TOPIC = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_TOPIC"
TABLE_TOPIC = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOPIC"

TABLE_CONTENT_COMPANY = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_COMPANY"
TABLE_COMPANY = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY"

TABLE_CONTENT_SOLUTION = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_SOLUTION"
)

TABLE_SOLUTION = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION"

TABLE_CONTENT_CONCEPT = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_CONCEPT"
)

TABLE_CONCEPT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONCEPT"


# ============================================================
# LIST CONTENTS (CURATOR FEED)
# ============================================================

def list_contents(
    limit: int = 20,
    offset: int = 0,
    topic_id: Optional[str] = None,
    content_type: Optional[str] = None,
):

    params = {
        "limit": limit,
        "offset": offset,
    }

    join = ""
    where_topic = ""
    where_content_type = ""

    # ============================================================
    # TOPIC FILTER
    # ============================================================

    if topic_id:

        join = f"""
            JOIN `{TABLE_CONTENT_TOPIC}` ct
              ON c.ID_CONTENT = ct.ID_CONTENT
        """

        where_topic = "AND ct.ID_TOPIC = @topic_id"

        params["topic_id"] = topic_id

    # ============================================================
    # CONTENT TYPE FILTER
    # ============================================================

    if content_type:

        where_content_type = """
            AND c.CONTENT_TYPE = @content_type
        """

        params["content_type"] = content_type

    # ============================================================
    # QUERY
    # ============================================================

    sql = f"""
        SELECT
            c.ID_CONTENT,
            c.TITLE,
            c.EXCERPT,
            c.CONTENT_TYPE,
            c.SIGNAL_ANALYTIQUE,
            c.PUBLISHED_AT

        FROM `{TABLE_CONTENT}` c

        {join}

        WHERE
            c.STATUS = 'PUBLISHED'
            AND c.IS_ACTIVE = TRUE

            {where_topic}
            {where_content_type}

        ORDER BY c.PUBLISHED_AT DESC

        LIMIT @limit
        OFFSET @offset
    """

    rows = query_bq(sql, params)

    # ============================================================
    # RETURN
    # ============================================================

    return [
        {
            "id": r["ID_CONTENT"],

            "title": r["TITLE"],

            "excerpt": r.get("EXCERPT"),

            "content_type": (
                r.get("CONTENT_TYPE")
                or "ANALYSIS"
            ),

            # 🔥 utilisé rapidement côté FE
            "is_news": (
                (r.get("CONTENT_TYPE") or "ANALYSIS")
                == "NEWS"
            ),

            "is_analysis": (
                (r.get("CONTENT_TYPE") or "ANALYSIS")
                == "ANALYSIS"
            ),

            "signal": r.get("SIGNAL_ANALYTIQUE"),

            "published_at": r["PUBLISHED_AT"],
        }
        for r in rows
    ]


# ============================================================
# READ CONTENT (DRAWER CURATOR)
# ============================================================

def get_content(id_content: str) -> Dict:

    rows = query_bq(
        f"""
        SELECT *
        FROM `{TABLE_CONTENT_ENRICHED}`
        WHERE id_content = @id_content
        LIMIT 1
        """,
        {"id_content": id_content},
    )

    if not rows:
        return None

    r = rows[0]

    content_type = (
        r.get("content_type")
        or "ANALYSIS"
    )

    # ============================================================
    # RETURN
    # ============================================================

    return {

        # ========================================================
        # CORE
        # ========================================================

        "id_content": r.get("id_content"),

        "title": r.get("title"),

        "excerpt": r.get("excerpt"),

        "content_body": r.get("content_body"),

        "published_at": r.get("published_at"),

        # ========================================================
        # CONTENT TYPE
        # ========================================================

        "content_type": content_type,

        # 🔥 très utile FE immédiatement
        "is_news": content_type == "NEWS",

        "is_analysis": content_type == "ANALYSIS",

        # ========================================================
        # ANALYSIS
        # ========================================================

        "signal": r.get("signal_analytique"),

        "mecanique_expliquee": r.get("mecanique_expliquee"),

        "enjeu_strategique": r.get("enjeu_strategique"),

        "point_de_friction": r.get("point_de_friction"),

        # ========================================================
        # RAW EXTRACTIONS
        # ========================================================

        "chiffres": r.get("chiffres") or [],

        "acteurs_cites": r.get("acteurs_cites") or [],

        "concepts_llm": r.get("concepts_llm") or [],

        # ========================================================
        # ENRICHED RELATIONS
        # ========================================================

        "topics": r.get("topics") or [],

        "companies": r.get("companies") or [],

        "solutions": r.get("solutions") or [],

        "concepts": r.get("concepts") or [],

        "universes": r.get("universes") or [],
    }
