from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import query_bq

# ============================================================
# TABLES
# ============================================================

TABLE_CONTENT = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"
)

TABLE_CONTENT_COMPANY = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_COMPANY"
)

TABLE_CONTENT_SOLUTION = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_SOLUTION"
)

TABLE_CONTENT_ENRICHED = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_ENRICHED"
)

TABLE_COMPANY_ALIAS = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY_ALIAS"
)

TABLE_SOLUTION_ALIAS = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION_ALIAS"
)


# ============================================================
# INTERNAL
# ============================================================

def _run_operation(
    sql: str,
    message: str,
):

    query_bq(sql)

    return {
        "status": "ok",
        "message": message,
    }


# ============================================================
# PUBLISHING
# ============================================================

def publish_all_drafts():

    sql = f"""
    UPDATE `{TABLE_CONTENT}`

    SET
        STATUS = CASE
            WHEN COALESCE(
                TIMESTAMP(SOURCE_DATE),
                CURRENT_TIMESTAMP()
            ) <= CURRENT_TIMESTAMP()
                THEN 'PUBLISHED'
            ELSE 'SCHEDULED'
        END,

        PUBLISHED_AT = COALESCE(
            TIMESTAMP(SOURCE_DATE),
            CURRENT_TIMESTAMP()
        ),

        UPDATED_AT = CURRENT_TIMESTAMP()

    WHERE STATUS = 'DRAFT'
    """

    return _run_operation(
        sql,
        "All draft contents have been published.",
    )


# ============================================================
# MAINTENANCE
# ============================================================

def rebuild_content_company():

    sql = f"""
    INSERT INTO `{TABLE_CONTENT_COMPANY}` (
        ID_CONTENT,
        ID_COMPANY
    )

    SELECT DISTINCT
        c.ID_CONTENT,
        a.ID_COMPANY

    FROM `{TABLE_CONTENT}` c,
    UNNEST(c.ACTEURS_CITES) AS raw

    JOIN `{TABLE_COMPANY_ALIAS}` a
      ON REGEXP_REPLACE(
            UPPER(TRIM(raw)),
            r'[^A-Z0-9 ]',
            ''
         )
       =
         REGEXP_REPLACE(
            UPPER(TRIM(a.ALIAS)),
            r'[^A-Z0-9 ]',
            ''
         )

    WHERE raw IS NOT NULL
      AND TRIM(raw) != ""

      AND NOT EXISTS (

          SELECT 1

          FROM `{TABLE_CONTENT_COMPANY}` existing

          WHERE
              existing.ID_CONTENT = c.ID_CONTENT
          AND existing.ID_COMPANY = a.ID_COMPANY

      )
    """

    return _run_operation(
        sql,
        "Content → Company rebuilt.",
    )


# ============================================================

def rebuild_content_solution():

    sql = f"""
    INSERT INTO `{TABLE_CONTENT_SOLUTION}` (
        ID_CONTENT,
        ID_SOLUTION
    )

    SELECT DISTINCT
        c.ID_CONTENT,
        a.ID_SOLUTION

    FROM `{TABLE_CONTENT}` c,

    UNNEST(
        ARRAY_CONCAT(
            IFNULL(c.SOLUTIONS_LLM, []),
            IFNULL(c.ACTEURS_CITES, [])
        )
    ) AS raw

    JOIN `{TABLE_SOLUTION_ALIAS}` a
      ON REGEXP_REPLACE(
            UPPER(TRIM(raw)),
            r'[^A-Z0-9 ]',
            ''
         )
       =
         REGEXP_REPLACE(
            UPPER(TRIM(a.ALIAS)),
            r'[^A-Z0-9 ]',
            ''
         )

    WHERE raw IS NOT NULL
      AND TRIM(raw) != ""

      AND NOT EXISTS (

          SELECT 1

          FROM `{TABLE_CONTENT_SOLUTION}` existing

          WHERE
              existing.ID_CONTENT = c.ID_CONTENT
          AND existing.ID_SOLUTION = a.ID_SOLUTION

      )
    """

    return _run_operation(
        sql,
        "Content → Solution rebuilt.",
    )
