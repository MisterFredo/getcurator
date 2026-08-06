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
    id_primary_company: Optional[str] = None,
):

    params = {
        "limit": limit,
        "offset": offset,
    }

    join = ""

    where_topic = ""
    where_primary_company = ""

    # ============================================================
    # TOPIC FILTER
    # ============================================================

    if topic_id:

        join += f"""
            JOIN `{TABLE_CONTENT_TOPIC}` ct
              ON c.ID_CONTENT = ct.ID_CONTENT
        """

        where_topic = "AND ct.ID_TOPIC = @topic_id"

        params["topic_id"] = topic_id


    # ============================================================
    # PRIMARY COMPANY FILTER
    # ============================================================

    if id_primary_company:

        where_primary_company = """
            AND c.ID_PRIMARY_COMPANY = @id_primary_company
        """

        params["id_primary_company"] = id_primary_company

    # ============================================================
    # QUERY
    # ============================================================

    sql = f"""
        SELECT
            c.ID_CONTENT,

            c.TITLE,
            c.TITLE_EN,

            c.EXCERPT,
            c.EXCERPT_EN,

            -- 🔥 NEW
            c.ID_PRIMARY_COMPANY,

            pc.NAME AS PRIMARY_COMPANY_NAME,

            c.SIGNAL_ANALYTIQUE,

            c.PUBLISHED_AT

        FROM `{TABLE_CONTENT}` c

        -- 🔥 NEW
        LEFT JOIN `{TABLE_COMPANY}` pc
          ON c.ID_PRIMARY_COMPANY = pc.ID_COMPANY

        {join}

        WHERE
            c.STATUS = 'PUBLISHED'
            AND c.IS_ACTIVE = TRUE

            {where_topic}

            {where_primary_company}

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
            "title_en": r["TITLE_EN"],

            "excerpt": r.get("EXCERPT"),
            "excerpt_en": r.get("EXCERPT_EN"),

            # 🔥 NEW
            "id_primary_company": r.get(
                "ID_PRIMARY_COMPANY"
            ),

            "primary_company_name": r.get(
                "PRIMARY_COMPANY_NAME"
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


    # ============================================================
    # PRIMARY COMPANY
    # ============================================================

    primary_company = None

    id_primary_company = r.get(
        "id_primary_company"
    )

    companies = r.get("companies") or []

    if id_primary_company:

        primary_company = next(
            (
                c for c in companies
                if (
                    c.get("id_company")
                    == id_primary_company
                )
            ),
            None
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
        "title_en": r.get("title_en"),

        "excerpt": r.get("excerpt"),
        "excerpt_en": r.get("excerpt_en"),

        "content_body": r.get("content_body"),

        "published_at": r.get("published_at"),


        # ========================================================
        # PRIMARY COMPANY
        # ========================================================

        "id_primary_company": id_primary_company,

        "primary_company": primary_company,

        # ========================================================
        # ANALYSIS
        # ========================================================

        "signal": r.get("signal_analytique"),

        "mecanique_expliquee": r.get(
            "mecanique_expliquee"
        ),

        "enjeu_strategique": r.get(
            "enjeu_strategique"
        ),

        "point_de_friction": r.get(
            "point_de_friction"
        ),

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

        "companies": companies,

        "solutions": r.get("solutions") or [],

        "concepts": r.get("concepts") or [],

        "universes": r.get("universes") or [],
    }

# ============================================================
# LIST CONTENTS (PUBLIC) : MOVE FROM SERVICE
# ============================================================

def list_contents():

    rows = query_bq(
        f"""
        SELECT
          c.ID_CONTENT,

          -- 🔥 NEW
          c.ID_PRIMARY_COMPANY,

          pc.NAME AS PRIMARY_COMPANY_NAME,

          c.TITLE,
          c.TITLE_EN,
          c.EXCERPT,
          c.EXCERPT_EN,
          c.SOURCE_URL,
          c.SOURCE_TITLE,
          c.PUBLISHED_AT

        FROM `{TABLE_CONTENT}` c

        -- 🔥 NEW
        LEFT JOIN `{TABLE_COMPANY}` pc
          ON c.ID_PRIMARY_COMPANY = pc.ID_COMPANY

        WHERE
          c.STATUS = 'PUBLISHED'
          AND c.IS_ACTIVE = TRUE

        ORDER BY c.PUBLISHED_AT DESC
        """
    )

    def map_dt(value):
        return value.isoformat() if value else None

    return [
        {
            "id_content": r["ID_CONTENT"],
            "source_url": r.get("SOURCE_URL"),
            "source_title": r.get("SOURCE_TITLE"),

            # 🔥 NEW
            "id_primary_company": r.get(
                "ID_PRIMARY_COMPANY"
            ),

            "primary_company_name": r.get(
                "PRIMARY_COMPANY_NAME"
            ),

            "title": r["TITLE"],
            "title_en": r["TITLE_EN"],

            "excerpt": r.get("EXCERPT"),
            "excerpt_en": r.get("EXCERPT_EN"),

            "published_at": map_dt(
                r.get("PUBLISHED_AT")
            ),
        }
        for r in rows
    ]

# ============================================================
# GET CONTENT MOVE FROM SERVICE
# ============================================================

def get_content(id_content: str):

    rows = query_bq(
        f"""
        SELECT
          ID_CONTENT,

          -- 🔥 NEW
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
        WHERE ID_CONTENT = @id
        LIMIT 1
        """,
        {"id": id_content},
    )

    if not rows:
        return None

    row = rows[0]

    def map_dt(value):
        return value.isoformat() if value else None

    content = {
        "id_content": row["ID_CONTENT"],

        # 🔥 NEW
        "id_primary_company": row.get("ID_PRIMARY_COMPANY"),

        "status": row.get("STATUS"),
        "source_id": row.get("SOURCE_ID"),
        "id_raw": row.get("ID_RAW"),
        "source_url": row.get("SOURCE_URL"),
        "source_title": row.get("SOURCE_TITLE"),

        "title": row.get("TITLE"),
        "title_en": row.get("TITLE_EN"),
        "excerpt": row.get("EXCERPT"),
        "excerpt_en": row.get("EXCERPT_EN"),
        "content_body": row.get("CONTENT_BODY"),

        "chiffres": row.get("CHIFFRES") or [],
        "acteurs_cites": row.get("ACTEURS_CITES") or [],

        "concepts_llm": row.get("CONCEPTS_LLM") or [],
        "solutions_llm": row.get("SOLUTIONS_LLM") or [],
        "topics_llm": row.get("TOPICS_LLM") or [],

        "mecanique_expliquee": row.get("MECANIQUE_EXPLIQUEE"),
        "enjeu_strategique": row.get("ENJEU_STRATEGIQUE"),
        "point_de_friction": row.get("POINT_DE_FRICTION"),
        "signal_analytique": row.get("SIGNAL_ANALYTIQUE"),

        "published_at": map_dt(row.get("PUBLISHED_AT")),
    }

    # ============================================================
    # RELATIONS — MAPPING SNAKE_CASE
    # ============================================================

    topic_rows = query_bq(
        f"""
        SELECT T.ID_TOPIC, T.LABEL, T.TOPIC_AXIS
        FROM `{TABLE_CONTENT_TOPIC}` CT
        JOIN `{TABLE_TOPIC}` T
          ON CT.ID_TOPIC = T.ID_TOPIC
        WHERE CT.ID_CONTENT = @id
        """,
        {"id": id_content},
    )

    content["topics"] = [
        {
            "id_topic": r["ID_TOPIC"],
            "label": r["LABEL"],
            "topic_axis": r.get("TOPIC_AXIS"),
        }
        for r in topic_rows
    ]

    company_rows = query_bq(
        f"""
        SELECT C.ID_COMPANY, C.NAME
        FROM `{TABLE_CONTENT_COMPANY}` CC
        JOIN `{TABLE_COMPANY}` C
          ON CC.ID_COMPANY = C.ID_COMPANY
        WHERE CC.ID_CONTENT = @id
        """,
        {"id": id_content},
    )

    content["companies"] = [
        {
            "id_company": r["ID_COMPANY"],
            "name": r["NAME"],
        }
        for r in company_rows
    ]

    # ============================================================
    # PRIMARY COMPANY
    # ============================================================

    primary_company = next(
        (
            c for c in content["companies"]
            if c["id_company"] == content["id_primary_company"]
        ),
        None
    )

    content["primary_company"] = primary_company

    concept_rows = query_bq(
        f"""
        SELECT C.ID_CONCEPT, C.LABEL
        FROM `{TABLE_CONTENT_CONCEPT}` CC
        JOIN `{TABLE_CONCEPT}` C
          ON CC.ID_CONCEPT = C.ID_CONCEPT
        WHERE CC.ID_CONTENT = @id
        """,
        {"id": id_content},
    )

    content["concepts"] = [
        {
            "id_concept": r["ID_CONCEPT"],
            "label": r["LABEL"],
        }
        for r in concept_rows
    ]

    solution_rows = query_bq(
        f"""
        SELECT S.ID_SOLUTION, S.NAME
        FROM `{TABLE_CONTENT_SOLUTION}` CS
        JOIN `{TABLE_SOLUTION}` S
          ON CS.ID_SOLUTION = S.ID_SOLUTION
        WHERE CS.ID_CONTENT = @id
        """,
        {"id": id_content},
    )

    content["solutions"] = [
        {
            "id_solution": r["ID_SOLUTION"],
            "name": r["NAME"],
        }
        for r in solution_rows
    ]

    return content
