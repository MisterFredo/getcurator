from typing import List, Dict, Optional

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq


TABLE_CONTENT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"
TABLE_CONTENT_TOPIC = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_TOPIC"
TABLE_TOPIC = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOPIC"

TABLE_CONTENT_COMPANY = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_COMPANY"
TABLE_COMPANY = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY"

TABLE_CONTENT_SOLUTION = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_SOLUTION"
TABLE_SOLUTION = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION"

# 🔥 NEW
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
        SELECT
            ID_CONTENT,
            TITLE,
            SIGNAL_ANALYTIQUE,
            EXCERPT,
            CONCEPTS_LLM,
            CONTENT_BODY,
            CHIFFRES,
            ACTEURS_CITES,
            PUBLISHED_AT
        FROM {TABLE_CONTENT}
        WHERE
            ID_CONTENT = @id_content
            AND STATUS = 'PUBLISHED'
            AND IS_ACTIVE = TRUE
        LIMIT 1
        """,
        {"id_content": id_content},
    )

    if not rows:
        return None

    r = rows[0]

    # ============================================================
    # TOPICS
    # ============================================================

    topic_rows = query_bq(
        f"""
        SELECT T.ID_TOPIC, T.LABEL
        FROM {TABLE_CONTENT_TOPIC} CT
        JOIN {TABLE_TOPIC} T
          ON CT.ID_TOPIC = T.ID_TOPIC
        WHERE CT.ID_CONTENT = @id
        """,
        {"id": id_content},
    )

    # ============================================================
    # COMPANIES
    # ============================================================

    company_rows = query_bq(
        f"""
        SELECT C.ID_COMPANY, C.NAME
        FROM {TABLE_CONTENT_COMPANY} CC
        JOIN {TABLE_COMPANY} C
          ON CC.ID_COMPANY = C.ID_COMPANY
        WHERE CC.ID_CONTENT = @id
        """,
        {"id": id_content},
    )

    # ============================================================
    # SOLUTIONS
    # ============================================================

    solution_rows = query_bq(
        f"""
        SELECT S.ID_SOLUTION, S.NAME
        FROM {TABLE_CONTENT_SOLUTION} CS
        JOIN {TABLE_SOLUTION} S
          ON CS.ID_SOLUTION = S.ID_SOLUTION
        WHERE CS.ID_CONTENT = @id
        """,
        {"id": id_content},
    )

    # ============================================================
    # 🔥 CONCEPTS STRUCTURÉS (NOUVEAU)
    # ============================================================

    concept_rows = query_bq(
        f"""
        SELECT C.ID_CONCEPT, C.LABEL
        FROM {TABLE_CONTENT_CONCEPT} CC
        JOIN {TABLE_CONCEPT} C
          ON CC.ID_CONCEPT = C.ID_CONCEPT
        WHERE CC.ID_CONTENT = @id
        """,
        {"id": id_content},
    )

    return {
        "id_content": r["ID_CONTENT"],
        "title": r["TITLE"],
        "signal": r.get("SIGNAL_ANALYTIQUE"),
        "excerpt": r.get("EXCERPT"),

        # 🔥 LLM (suggestion)
        "concepts_llm": r.get("CONCEPTS_LLM") or [],

        "content_body": r.get("CONTENT_BODY"),
        "chiffres": r.get("CHIFFRES") or [],
        "acteurs_cites": r.get("ACTEURS_CITES") or [],
        "published_at": r["PUBLISHED_AT"],

        # ========================================================
        # ENRICHISSEMENTS
        # ========================================================

        "topics": [
            {
                "id_topic": t["ID_TOPIC"],
                "label": t["LABEL"],
            }
            for t in topic_rows
        ],

        "companies": [
            {
                "id_company": c["ID_COMPANY"],
                "name": c["NAME"],
            }
            for c in company_rows
        ],

        # 🔥 STRUCTURÉ = vérité métier
        "concepts": [
            {
                "id_concept": c["ID_CONCEPT"],
                "label": r["LABEL"],
            }
            for c in concept_rows
        ],

        "solutions": [
            {
                "id_solution": s["ID_SOLUTION"],
                "name": s["NAME"],
            }
            for s in solution_rows
        ],
    }
