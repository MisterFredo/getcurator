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

TABLE_COMPANY_ALIAS = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY_ALIAS"
)

TABLE_SOLUTION_ALIAS = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION_ALIAS"
)

TABLE_ALIAS_REJECTED = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_ALIAS_REJECTED"
)

# ============================================================
# DUPLICATE TITLES
# ============================================================

def get_duplicate_titles():

    sql = f"""
    WITH ranked AS (

      SELECT
        ID_CONTENT,
        TITLE,
        SOURCE_URL,
        PUBLISHED_AT,
        CREATED_AT,

        ROW_NUMBER() OVER (
          PARTITION BY TITLE
          ORDER BY
            PUBLISHED_AT DESC,
            CREATED_AT DESC
        ) AS rn

      FROM `{TABLE_CONTENT}`

      WHERE TITLE IS NOT NULL
        AND TRIM(TITLE) != ""

    )

    SELECT *

    FROM ranked

    WHERE rn > 1

    ORDER BY TITLE
    """

    return query_bq(sql)


# ============================================================
# UNMATCHED COMPANIES
# ============================================================

def get_unmatched_companies():

    sql = f"""
    SELECT
      raw AS value,
      COUNT(*) AS count

    FROM `{TABLE_CONTENT}`,
    UNNEST(ACTEURS_CITES) AS raw

    WHERE raw IS NOT NULL
      AND TRIM(raw) != ""

      AND REGEXP_REPLACE(
            UPPER(TRIM(raw)),
            r'[^A-Z0-9 ]',
            ''
          ) NOT IN (

            SELECT DISTINCT
              REGEXP_REPLACE(
                UPPER(TRIM(ALIAS)),
                r'[^A-Z0-9 ]',
                ''
              )

            FROM `{TABLE_COMPANY_ALIAS}`

            UNION DISTINCT

            SELECT DISTINCT
              REGEXP_REPLACE(
                UPPER(TRIM(ALIAS)),
                r'[^A-Z0-9 ]',
                ''
              )

            FROM `{TABLE_ALIAS_REJECTED}`

            WHERE ENTITY_TYPE = 'company'

          )

    GROUP BY raw

    ORDER BY count DESC
    """

    return query_bq(sql)


# ============================================================
# UNMATCHED SOLUTIONS
# ============================================================

def get_unmatched_solutions():

    sql = f"""
    SELECT
      raw AS value,
      COUNT(*) AS count

    FROM `{TABLE_CONTENT}`,
    UNNEST(SOLUTIONS_LLM) AS raw

    WHERE raw IS NOT NULL
      AND TRIM(raw) != ""

      AND REGEXP_REPLACE(
            UPPER(TRIM(raw)),
            r'[^A-Z0-9 ]',
            ''
          ) NOT IN (

            SELECT DISTINCT
              REGEXP_REPLACE(
                UPPER(TRIM(ALIAS)),
                r'[^A-Z0-9 ]',
                ''
              )

            FROM `{TABLE_SOLUTION_ALIAS}`

            UNION DISTINCT

            SELECT DISTINCT
              REGEXP_REPLACE(
                UPPER(TRIM(ALIAS)),
                r'[^A-Z0-9 ]',
                ''
              )

            FROM `{TABLE_ALIAS_REJECTED}`

            WHERE ENTITY_TYPE = 'solution'

          )

    GROUP BY raw

    ORDER BY count DESC
    """

    return query_bq(sql)


# ============================================================
# NUMBERS STRUCTURE
# ============================================================

def get_numbers_structure():

    sql = f"""
    WITH base AS (

      SELECT
        c.ID_CONTENT,
        chiffre AS raw_line,
        SPLIT(chiffre, "|") AS parts

      FROM `{TABLE_CONTENT}` c,
      UNNEST(c.CHIFFRES) AS chiffre

      WHERE c.CHIFFRES IS NOT NULL

    )

    SELECT

      ID_CONTENT,

      raw_line,

      ARRAY_LENGTH(parts) AS nb_parts,

      CASE
        WHEN ARRAY_LENGTH(parts) = 6 THEN "STRUCTURED_6"
        WHEN ARRAY_LENGTH(parts) = 7 THEN "STRUCTURED_7"
        ELSE "NOT_STRUCTURED"
      END AS structure_status,

      TRIM(parts[SAFE_OFFSET(0)]) AS label,

      SAFE_CAST(
        TRIM(parts[SAFE_OFFSET(1)])
        AS FLOAT64
      ) AS value,

      TRIM(parts[SAFE_OFFSET(2)]) AS unit_raw,

      TRIM(parts[SAFE_OFFSET(3)]) AS actor,

      TRIM(parts[SAFE_OFFSET(4)]) AS market,

      TRIM(parts[SAFE_OFFSET(5)]) AS period,

      TRIM(parts[SAFE_OFFSET(6)]) AS type,

      SAFE_CAST(
        TRIM(parts[SAFE_OFFSET(1)])
        AS FLOAT64
      ) IS NOT NULL AS valid_value,

      parts[SAFE_OFFSET(2)] IS NOT NULL AS has_unit,

      parts[SAFE_OFFSET(3)] IS NOT NULL AS has_actor,

      parts[SAFE_OFFSET(5)] IS NOT NULL AS has_period,

      parts[SAFE_OFFSET(6)] IS NOT NULL AS has_type

    FROM base
    """

    return query_bq(sql)
