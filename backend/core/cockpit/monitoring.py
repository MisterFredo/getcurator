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

TABLE_CONTENT_RAW = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_RAW"
)

# ============================================================
# DESTOCK STATUS
# ============================================================

def get_destock_status():

    sql = f"""
    SELECT

      CURRENT_TIMESTAMP() AS run_time,

      COUNT(*) AS total,

      COUNTIF(STATUS = 'STORED') AS stored,

      COUNTIF(STATUS = 'PROCESSING') AS processing,

      COUNTIF(STATUS = 'PROCESSED') AS processed,

      COUNTIF(STATUS = 'ERROR') AS errors,

      ROUND(
        100 * COUNTIF(STATUS = 'PROCESSED')
        / NULLIF(COUNT(*), 0),
        2
      ) AS progress_pct

    FROM `{TABLE_CONTENT_RAW}`
    """

    rows = query_bq(sql)

    if not rows:
        return {}

    return rows[0]


# ============================================================
# TRANSLATION STATUS
# ============================================================

def get_translation_status():

    sql = f"""
    SELECT

      COUNT(*) AS total_contents,

      COUNTIF(
        TITLE_EN IS NOT NULL
        AND TRIM(TITLE_EN) != ""
      ) AS title_en_done,

      COUNTIF(
        EXCERPT_EN IS NOT NULL
        AND TRIM(EXCERPT_EN) != ""
      ) AS excerpt_en_done,

      COUNTIF(
        TITLE_EN IS NOT NULL
        AND TRIM(TITLE_EN) != ""
        AND EXCERPT_EN IS NOT NULL
        AND TRIM(EXCERPT_EN) != ""
      ) AS fully_translated,

      COUNTIF(
        TITLE_EN IS NULL
        OR TRIM(TITLE_EN) = ""
        OR EXCERPT_EN IS NULL
        OR TRIM(EXCERPT_EN) = ""
      ) AS missing_translation,

      ROUND(
        100 * COUNTIF(
          TITLE_EN IS NOT NULL
          AND TRIM(TITLE_EN) != ""
          AND EXCERPT_EN IS NOT NULL
          AND TRIM(EXCERPT_EN) != ""
        )
        / COUNT(*),
        2
      ) AS pct_fully_translated

    FROM `{TABLE_CONTENT}`

    WHERE IS_ACTIVE = TRUE
    """

    rows = query_bq(sql)

    if not rows:
        return {}

    return rows[0]


# ============================================================
# MONITORING
# ============================================================

def get_monitoring():

    return {
        "destock": get_destock_status(),
        "translation": get_translation_status(),
    }
