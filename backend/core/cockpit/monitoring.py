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

      COUNTIF(
        STATUS = 'STORED'
      ) AS stored,

      COUNTIF(
        STATUS = 'PROCESSING'
      ) AS processing,

      COUNTIF(
        STATUS = 'PROCESSED'
      ) AS processed,

      COUNTIF(
        STATUS = 'ERROR'
      ) AS errors,

      ROUND(
        100
        * COUNTIF(
            STATUS = 'PROCESSED'
          )
        / NULLIF(
            COUNT(*),
            0
          ),
        2
      ) AS progress_pct

    FROM `{TABLE_CONTENT_RAW}`
    """

    rows = query_bq(
        sql
    )

    if not rows:
        return {}

    return rows[0]


# ============================================================
# TRANSLATION STATUS
# ============================================================

def get_translation_status():

    sql = f"""
    WITH content_flags AS (

      SELECT

        ID_CONTENT,

        -- ===================================================
        -- ENGLISH SOURCE
        -- ===================================================

        (
          NULLIF(
            TRIM(TITLE_EN),
            ''
          ) IS NOT NULL
        ) AS has_title_en,

        (
          NULLIF(
            TRIM(EXCERPT_EN),
            ''
          ) IS NOT NULL
        ) AS has_excerpt_en,

        (
          NULLIF(
            TRIM(CONTENT_BODY_EN),
            ''
          ) IS NOT NULL
        ) AS has_content_body_en,

        (
          NULLIF(
            TRIM(SIGNAL_ANALYTIQUE_EN),
            ''
          ) IS NOT NULL
        ) AS has_signal_en,

        (
          NULLIF(
            TRIM(MECANIQUE_EXPLIQUEE_EN),
            ''
          ) IS NOT NULL
        ) AS has_mecanique_en,

        (
          NULLIF(
            TRIM(ENJEU_STRATEGIQUE_EN),
            ''
          ) IS NOT NULL
        ) AS has_enjeu_en,

        (
          NULLIF(
            TRIM(POINT_DE_FRICTION_EN),
            ''
          ) IS NOT NULL
        ) AS has_friction_en,

        -- ===================================================
        -- FRENCH TARGET
        -- ===================================================

        (
          NULLIF(
            TRIM(TITLE),
            ''
          ) IS NOT NULL
        ) AS has_title_fr,

        (
          NULLIF(
            TRIM(EXCERPT),
            ''
          ) IS NOT NULL
        ) AS has_excerpt_fr,

        (
          NULLIF(
            TRIM(CONTENT_BODY),
            ''
          ) IS NOT NULL
        ) AS has_content_body_fr,

        (
          NULLIF(
            TRIM(SIGNAL_ANALYTIQUE),
            ''
          ) IS NOT NULL
        ) AS has_signal_fr,

        (
          NULLIF(
            TRIM(MECANIQUE_EXPLIQUEE),
            ''
          ) IS NOT NULL
        ) AS has_mecanique_fr,

        (
          NULLIF(
            TRIM(ENJEU_STRATEGIQUE),
            ''
          ) IS NOT NULL
        ) AS has_enjeu_fr,

        (
          NULLIF(
            TRIM(POINT_DE_FRICTION),
            ''
          ) IS NOT NULL
        ) AS has_friction_fr

      FROM `{TABLE_CONTENT}`

      WHERE
        IS_ACTIVE = TRUE
    ),

    translation_flags AS (

      SELECT

        *,

        (
          has_title_en
          OR has_excerpt_en
          OR has_content_body_en
          OR has_signal_en
          OR has_mecanique_en
          OR has_enjeu_en
          OR has_friction_en
        ) AS has_english_source,

        (
          (
            NOT has_title_en
            OR has_title_fr
          )
          AND (
            NOT has_excerpt_en
            OR has_excerpt_fr
          )
          AND (
            NOT has_content_body_en
            OR has_content_body_fr
          )
          AND (
            NOT has_signal_en
            OR has_signal_fr
          )
          AND (
            NOT has_mecanique_en
            OR has_mecanique_fr
          )
          AND (
            NOT has_enjeu_en
            OR has_enjeu_fr
          )
          AND (
            NOT has_friction_en
            OR has_friction_fr
          )
        ) AS is_fully_translated

      FROM content_flags
    )

    SELECT

      COUNT(*) AS total_contents,

      COUNTIF(
        has_english_source
      ) AS english_source_ready,

      COUNTIF(
        NOT has_english_source
      ) AS english_source_missing,

      COUNTIF(
        has_title_en
        AND has_title_fr
      ) AS title_fr_done,

      COUNTIF(
        has_excerpt_en
        AND has_excerpt_fr
      ) AS excerpt_fr_done,

      COUNTIF(
        has_content_body_en
        AND has_content_body_fr
      ) AS content_body_fr_done,

      COUNTIF(
        has_signal_en
        AND has_signal_fr
      ) AS signal_fr_done,

      COUNTIF(
        has_mecanique_en
        AND has_mecanique_fr
      ) AS mecanique_fr_done,

      COUNTIF(
        has_enjeu_en
        AND has_enjeu_fr
      ) AS enjeu_fr_done,

      COUNTIF(
        has_friction_en
        AND has_friction_fr
      ) AS friction_fr_done,

      COUNTIF(
        has_english_source
        AND is_fully_translated
      ) AS fully_translated,

      COUNTIF(
        has_english_source
        AND NOT is_fully_translated
      ) AS missing_translation,

      ROUND(
        100
        * COUNTIF(
            has_english_source
            AND is_fully_translated
          )
        / NULLIF(
            COUNTIF(
              has_english_source
            ),
            0
          ),
        2
      ) AS pct_fully_translated

    FROM translation_flags
    """

    rows = query_bq(
        sql
    )

    if not rows:
        return {}

    return rows[0]


# ============================================================
# MONITORING
# ============================================================

def get_monitoring():

    return {

        "destock":
            get_destock_status(),

        "translation":
            get_translation_status(),

    }
