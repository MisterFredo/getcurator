from typing import List, Dict, Optional

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq


TABLE_CONTENT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"

# 🔥 NEW
TABLE_CONTENT_ENRICHED = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_ENRICHED"
)

TABLE_CONTENT_TOPIC = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_TOPIC"
TABLE_TOPIC = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOPIC"

TABLE_CONTENT_COMPANY = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_COMPANY"
TABLE_COMPANY = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY"

TABLE_CONTENT_SOLUTION = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_SOLUTION"
TABLE_SOLUTION = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION"

TABLE_CONTENT_CONCEPT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_CONCEPT"
TABLE_CONCEPT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONCEPT"


# ============================================================
# LIST CONTENTS (CURATOR FEED)
# ============================================================

def list_contents(
    limit: int = 20,
    offset: int = 0,
    topic_id: Optional[str] = None,
):

    params = {
        "limit": limit,
        "offset": offset,
    }

    join = ""
    where_topic = ""

    if topic_id:
        join = f"""
            JOIN {TABLE_CONTENT_TOPIC} ct
              ON c.ID_CONTENT = ct.ID_CONTENT
        """
        where_topic = "AND ct.ID_TOPIC = @topic_id"
        params["topic_id"] = topic_id

    sql = f"""
        SELECT
            c.ID_CONTENT,
            c.TITLE,
            c.EXCERPT,
            c.SIGNAL_ANALYTIQUE,
            c.PUBLISHED_AT
        FROM {TABLE_CONTENT} c
        {join}
        WHERE
            c.STATUS = 'PUBLISHED'
            AND c.IS_ACTIVE = TRUE
            {where_topic}
        ORDER BY c.PUBLISHED_AT DESC
        LIMIT @limit OFFSET @offset
    """

    rows = query_bq(sql, params)

    return [
        {
            "id": r["ID_CONTENT"],
            "title": r["TITLE"],
            "excerpt": r.get("EXCERPT"),
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

    return {
        "id_content": r.get("id_content"),

        "title": r.get("title"),

        "signal": r.get("signal_analytique"),

        "excerpt": r.get("excerpt"),

        # 🔥 LLM
        "concepts_llm": r.get("concepts_llm") or [],

        "content_body": r.get("content_body"),

        "chiffres": r.get("chiffres") or [],

        "acteurs_cites": r.get("acteurs_cites") or [],

        "published_at": r.get("published_at"),

        # ========================================================
        # ENRICHISSEMENTS DIRECTS
        # ========================================================

        "topics": r.get("topics") or [],

        "companies": r.get("companies") or [],

        "solutions": r.get("solutions") or [],

        "concepts": r.get("concepts") or [],

        "universes": r.get("universes") or [],
    }
