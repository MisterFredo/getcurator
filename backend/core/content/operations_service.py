from utils.bigquery_utils import query_bq

TABLE_CONTENT = \
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"

TABLE_CONTENT_COMPANY = \
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_COMPANY"

TABLE_COMPANY_ALIAS = \
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY_ALIAS"

# ============================================================
# REBUILD CONTENT → COMPANY
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

    query_bq(sql)

    return {
        "status": "ok",
        "message": "Content → Company rebuilt.",
    }
