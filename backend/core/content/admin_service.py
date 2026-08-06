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

# ============================================================
# TABLES
# ============================================================

TABLE_CONTENT = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"
)

TABLE_COMPANY = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY"
)

TABLE_SOURCE = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOURCE"
)

TABLE_CONTENT_RAW = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_RAW"
)

# ============================================================
# LIST CONTENTS ADMIN
# ============================================================

def list_contents_admin():

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

          c.STATUS,

          c.SOURCE_DATE,
          c.SOURCE_URL,
          c.SOURCE_TITLE,

          c.PUBLISHED_AT,
          c.UPDATED_AT

        FROM `{TABLE_CONTENT}` c

        -- 🔥 NEW
        LEFT JOIN `{TABLE_COMPANY}` pc
          ON c.ID_PRIMARY_COMPANY = pc.ID_COMPANY

        WHERE c.IS_ACTIVE = TRUE

        ORDER BY c.UPDATED_AT DESC
        """
    )

    return [

        {
            "id_content": r["ID_CONTENT"],

            # 🔥 NEW
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

            "excerpt": r["EXCERPT"],
            "excerpt_en": r["EXCERPT_EN"],

            "status": r["STATUS"],

            "source_date": (

                r["SOURCE_DATE"].isoformat()

                if r.get("SOURCE_DATE")

                else None
            ),

            "published_at": (

                r["PUBLISHED_AT"].isoformat()

                if r.get("PUBLISHED_AT")

                else None
            ),

            "updated_at": (

                r["UPDATED_AT"].isoformat()

                if r.get("UPDATED_AT")

                else None
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


def get_source_monitoring():

    from utils.bigquery_utils import query_bq

    query = """
    WITH ranked AS (

      SELECT
        r.SOURCE_ID,

        r.DATE_SOURCE,
        r.SOURCE_URL,
        r.SOURCE_TITLE,

        ROW_NUMBER() OVER (
          PARTITION BY r.SOURCE_ID
          ORDER BY r.DATE_SOURCE DESC
        ) AS rn

      FROM `adex-5555.RATECARD_PROD.RATECARD_CONTENT_RAW` r
    ),

    last_article AS (

      SELECT
        SOURCE_ID,
        DATE_SOURCE AS LAST_ARTICLE_DATE,
        SOURCE_URL AS LAST_ARTICLE_URL,
        SOURCE_TITLE AS LAST_ARTICLE_TITLE

      FROM ranked

      WHERE rn = 1
    ),

    agg AS (

      SELECT
        SOURCE_ID,

        MAX(CREATED_AT) AS LAST_IMPORT_AT,

        COUNTIF(
          CREATED_AT >= TIMESTAMP_SUB(
            CURRENT_TIMESTAMP(),
            INTERVAL 7 DAY
          )
        ) AS NB_IMPORTED_7D

      FROM `adex-5555.RATECARD_PROD.RATECARD_CONTENT_RAW`

      GROUP BY
        SOURCE_ID
    )

    SELECT

      s.SOURCE_ID,

      s.NAME AS SOURCE_NAME,

      la.LAST_ARTICLE_DATE,
      la.LAST_ARTICLE_URL,
      la.LAST_ARTICLE_TITLE,

      agg.LAST_IMPORT_AT,
      agg.NB_IMPORTED_7D

    FROM `adex-5555.RATECARD_PROD.RATECARD_SOURCE` s

    LEFT JOIN last_article la
      ON s.SOURCE_ID = la.SOURCE_ID

    LEFT JOIN agg
      ON s.SOURCE_ID = agg.SOURCE_ID

    ORDER BY agg.LAST_IMPORT_AT DESC
    """

    rows = query_bq(query)

    return rows
