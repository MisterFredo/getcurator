# ============================================================
# IMPORTS
# ============================================================

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
)
from typing import List, Dict, Optional

# ============================================================
# TABLES
# ============================================================

TABLE_CONTENT = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"
)

TABLE_CONTENT_TOPIC = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_TOPIC"
)

TABLE_CONTENT_COMPANY = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_COMPANY"
)

TABLE_CONTENT_CONCEPT = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_CONCEPT"
)

TABLE_CONTENT_SOLUTION = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_SOLUTION"
)

TABLE_CONTENT_RAW = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_RAW"
)

TABLE_TOPIC = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOPIC"
)

TABLE_COMPANY = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY"
)

TABLE_CONCEPT = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONCEPT"
)

TABLE_SOLUTION = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION"
)

TABLE_SOURCE = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOURCE"
)

# ============================================================
# DATETIME
# ============================================================

def _map_datetime(
    value,
):

    return (
        value.isoformat()
        if value
        else None
    )

# ============================================================
# LOAD RELATIONS
# ============================================================

def _load_content_relations(
    id_content: str,
) -> Dict:

    # ========================================================
    # TOPICS
    # ========================================================

    topic_rows = query_bq(
        f"""
        SELECT
            T.ID_TOPIC,
            T.LABEL,
            T.TOPIC_AXIS
        FROM `{TABLE_CONTENT_TOPIC}` CT
        JOIN `{TABLE_TOPIC}` T
          ON CT.ID_TOPIC = T.ID_TOPIC
        WHERE CT.ID_CONTENT = @id
        """,
        {
            "id": id_content,
        },
    )

    topics = [

        {
            "id_topic": r["ID_TOPIC"],
            "label": r["LABEL"],
            "topic_axis": r.get(
                "TOPIC_AXIS"
            ),
        }

        for r in topic_rows

    ]

    # ========================================================
    # COMPANIES
    # ========================================================

    company_rows = query_bq(
        f"""
        SELECT
            C.ID_COMPANY,
            C.NAME
        FROM `{TABLE_CONTENT_COMPANY}` CC
        JOIN `{TABLE_COMPANY}` C
          ON CC.ID_COMPANY = C.ID_COMPANY
        WHERE CC.ID_CONTENT = @id
        """,
        {
            "id": id_content,
        },
    )

    companies = [

        {
            "id_company": r["ID_COMPANY"],
            "name": r["NAME"],
        }

        for r in company_rows

    ]

    # ========================================================
    # SOLUTIONS
    # ========================================================

    solution_rows = query_bq(
        f"""
        SELECT
            S.ID_SOLUTION,
            S.NAME
        FROM `{TABLE_CONTENT_SOLUTION}` CS
        JOIN `{TABLE_SOLUTION}` S
          ON CS.ID_SOLUTION = S.ID_SOLUTION
        WHERE CS.ID_CONTENT = @id
        """,
        {
            "id": id_content,
        },
    )

    solutions = [

        {
            "id_solution": r["ID_SOLUTION"],
            "name": r["NAME"],
        }

        for r in solution_rows

    ]

    # ========================================================
    # CONCEPTS
    # ========================================================

    concept_rows = query_bq(
        f"""
        SELECT
            C.ID_CONCEPT,
            C.LABEL
        FROM `{TABLE_CONTENT_CONCEPT}` CC
        JOIN `{TABLE_CONCEPT}` C
          ON CC.ID_CONCEPT = C.ID_CONCEPT
        WHERE CC.ID_CONTENT = @id
        """,
        {
            "id": id_content,
        },
    )

    concepts = [

        {
            "id_concept": r["ID_CONCEPT"],
            "label": r["LABEL"],
        }

        for r in concept_rows

    ]

    return {

        "topics": topics,

        "companies": companies,

        "solutions": solutions,

        "concepts": concepts,

    }

# ============================================================
# LIST CONTENTS ADMIN
# ============================================================

# ============================================================
# LIST CONTENTS ADMIN
# ============================================================

def list_contents_admin():

    rows = query_bq(
        f"""
        SELECT
            c.ID_CONTENT,

            c.ID_PRIMARY_COMPANY,

            pc.NAME AS PRIMARY_COMPANY_NAME,

            c.TITLE,
            c.TITLE_EN,

            c.EXCERPT,
            c.EXCERPT_EN,

            c.STATUS,

            c.SOURCE_DATE,
            c.SOURCE_URL,
            c.SOURCE_TITLE,

            c.PUBLISHED_AT,
            c.UPDATED_AT

        FROM `{TABLE_CONTENT}` c

        LEFT JOIN `{TABLE_COMPANY}` pc
          ON c.ID_PRIMARY_COMPANY = pc.ID_COMPANY

        WHERE
            c.IS_ACTIVE = TRUE

        ORDER BY
            c.UPDATED_AT DESC
        """
    )

    return [

        {

            "id_content": r["ID_CONTENT"],

            "id_primary_company": r.get(
                "ID_PRIMARY_COMPANY"
            ),

            "primary_company_name": r.get(
                "PRIMARY_COMPANY_NAME"
            ),

            "source_url": r.get(
                "SOURCE_URL"
            ),

            "source_title": r.get(
                "SOURCE_TITLE"
            ),

            "title": r["TITLE"],
            "title_en": r["TITLE_EN"],

            "excerpt": r.get(
                "EXCERPT"
            ),

            "excerpt_en": r.get(
                "EXCERPT_EN"
            ),

            "status": r.get(
                "STATUS"
            ),

            "source_date": _map_datetime(
                r.get("SOURCE_DATE")
            ),

            "published_at": _map_datetime(
                r.get("PUBLISHED_AT")
            ),

            "updated_at": _map_datetime(
                r.get("UPDATED_AT")
            ),

        }

        for r in rows

    ]

# ============================================================
# GET CONTENT
# ============================================================

# ============================================================
# GET CONTENT ADMIN
# ============================================================

def get_content_admin(
    id_content: str,
):

    rows = query_bq(
        f"""
        SELECT
            ID_CONTENT,

            ID_PRIMARY_COMPANY,

            STATUS,
            SOURCE_ID,
            ID_RAW,

            SOURCE_URL,
            SOURCE_TITLE,

            TITLE,
            TITLE_EN,

            EXCERPT,
            EXCERPT_EN,

            CONTENT_BODY,

            CHIFFRES,
            ACTEURS_CITES,

            CONCEPTS_LLM,
            SOLUTIONS_LLM,
            TOPICS_LLM,

            MECANIQUE_EXPLIQUEE,
            ENJEU_STRATEGIQUE,
            POINT_DE_FRICTION,
            SIGNAL_ANALYTIQUE,

            PUBLISHED_AT

        FROM `{TABLE_CONTENT}`

        WHERE
            ID_CONTENT = @id

        LIMIT 1
        """,
        {
            "id": id_content,
        },
    )

    if not rows:
        return None

    row = rows[0]

    content = {

        # ====================================================
        # IDENTIFICATION
        # ====================================================

        "id_content": row["ID_CONTENT"],

        "id_primary_company": row.get(
            "ID_PRIMARY_COMPANY"
        ),

        "status": row.get(
            "STATUS"
        ),

        "source_id": row.get(
            "SOURCE_ID"
        ),

        "id_raw": row.get(
            "ID_RAW"
        ),

        # ====================================================
        # SOURCE
        # ====================================================

        "source_url": row.get(
            "SOURCE_URL"
        ),

        "source_title": row.get(
            "SOURCE_TITLE"
        ),

        # ====================================================
        # CONTENT
        # ====================================================

        "title": row.get(
            "TITLE"
        ),

        "title_en": row.get(
            "TITLE_EN"
        ),

        "excerpt": row.get(
            "EXCERPT"
        ),

        "excerpt_en": row.get(
            "EXCERPT_EN"
        ),

        "content_body": row.get(
            "CONTENT_BODY"
        ),

        # ====================================================
        # ANALYSIS
        # ====================================================

        "signal_analytique": row.get(
            "SIGNAL_ANALYTIQUE"
        ),

        "mecanique_expliquee": row.get(
            "MECANIQUE_EXPLIQUEE"
        ),

        "enjeu_strategique": row.get(
            "ENJEU_STRATEGIQUE"
        ),

        "point_de_friction": row.get(
            "POINT_DE_FRICTION"
        ),

        # ====================================================
        # RAW EXTRACTIONS
        # ====================================================

        "chiffres": row.get(
            "CHIFFRES"
        ) or [],

        "acteurs_cites": row.get(
            "ACTEURS_CITES"
        ) or [],

        "topics_llm": row.get(
            "TOPICS_LLM"
        ) or [],

        "solutions_llm": row.get(
            "SOLUTIONS_LLM"
        ) or [],

        "concepts_llm": row.get(
            "CONCEPTS_LLM"
        ) or [],

        # ====================================================
        # DATES
        # ====================================================

        "published_at": _map_datetime(
            row.get(
                "PUBLISHED_AT"
            )
        ),

    }

    # ========================================================
    # RELATIONS
    # ========================================================

    content.update(
        _load_content_relations(
            id_content,
        )
    )

    # ========================================================
    # PRIMARY COMPANY
    # ========================================================

    content["primary_company"] = next(
        (
            company
            for company in content["companies"]
            if (
                company["id_company"]
                == content["id_primary_company"]
            )
        ),
        None,
    )

    return content


# ============================================================
# CONTENT STATS
# ============================================================

def get_content_stats():

    sql = f"""
        SELECT

          COUNT(*) AS TOTAL,

          COUNTIF(
            STATUS = 'DRAFT'
          ) AS TOTAL_DRAFT,

          COUNTIF(
            STATUS = 'READY'
          ) AS TOTAL_READY,

          COUNTIF(
            STATUS = 'PUBLISHED'
          ) AS TOTAL_PUBLISHED,

          COUNTIF(
            STATUS = 'SCHEDULED'
          ) AS TOTAL_SCHEDULED,

          COUNTIF(
            STATUS = 'PUBLISHED'
            AND EXTRACT(YEAR FROM PUBLISHED_AT)
                = EXTRACT(YEAR FROM CURRENT_DATE())
          ) AS TOTAL_PUBLISHED_THIS_YEAR,

          COUNTIF(
            STATUS = 'PUBLISHED'
            AND EXTRACT(YEAR FROM PUBLISHED_AT)
                = EXTRACT(YEAR FROM CURRENT_DATE())
            AND EXTRACT(MONTH FROM PUBLISHED_AT)
                = EXTRACT(MONTH FROM CURRENT_DATE())
          ) AS TOTAL_PUBLISHED_THIS_MONTH

        FROM `{TABLE_CONTENT}`
    """

    rows = query_bq(sql)

    if not rows:

        return {
            "total": 0,
            "total_draft": 0,
            "total_ready": 0,
            "total_published": 0,
            "total_scheduled": 0,

            # 🔥 NEW

            "total_published_this_year": 0,
            "total_published_this_month": 0,
        }

    r = rows[0]

    return {

        "total": r.get("TOTAL", 0),

        "total_draft": r.get("TOTAL_DRAFT", 0),

        "total_ready": r.get("TOTAL_READY", 0),

        "total_published": r.get("TOTAL_PUBLISHED", 0),

        "total_scheduled": r.get("TOTAL_SCHEDULED", 0),

        # 🔥 NEW
        "total_published_this_year": r.get(
            "TOTAL_PUBLISHED_THIS_YEAR",
            0
        ),

        "total_published_this_month": r.get(
            "TOTAL_PUBLISHED_THIS_MONTH",
            0
        ),
    }
