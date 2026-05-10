from datetime import datetime, timezone

from config import BQ_PROJECT, BQ_DATASET

from utils.bigquery_utils import (
    query_bq,
)

# ============================================================
# TABLES
# ============================================================

TABLE_CONTENT = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"
)

TABLE_CONTENT_ENRICHED = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_ENRICHED"
)

TABLE_CONTENT_COMPANY = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_COMPANY"
)

TABLE_CONTENT_SOLUTION = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_SOLUTION"
)

TABLE_COMPANY_ALIAS = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY_ALIAS"
)

TABLE_SOLUTION_ALIAS = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION_ALIAS"
)


# ============================================================
# COMPANY MATCHING
# ============================================================

def sync_content_companies(
    id_content: str,
):

    # ========================================================
    # DELETE OLD RELATIONS
    # ========================================================

    query_bq(
        f"""
        DELETE FROM `{TABLE_CONTENT_COMPANY}`
        WHERE ID_CONTENT = @id_content
        """,
        {
            "id_content": id_content,
        }
    )

    # ========================================================
    # INSERT MATCHED COMPANIES
    # ========================================================

    query_bq(
        f"""
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

        WHERE
            c.ID_CONTENT = @id_content

            AND a.MATCH_STATUS = 'MATCH'

            AND raw IS NOT NULL

            AND TRIM(raw) != ''
        """,
        {
            "id_content": id_content,
        }
    )

    print(
        "✅ COMPANY SYNC DONE:",
        id_content,
    )


# ============================================================
# SOLUTION MATCHING
# ============================================================

def sync_content_solutions(
    id_content: str,
):

    # ========================================================
    # DELETE OLD RELATIONS
    # ========================================================

    query_bq(
        f"""
        DELETE FROM `{TABLE_CONTENT_SOLUTION}`
        WHERE ID_CONTENT = @id_content
        """,
        {
            "id_content": id_content,
        }
    )

    # ========================================================
    # INSERT MATCHED SOLUTIONS
    # ========================================================

    query_bq(
        f"""
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

        WHERE
            c.ID_CONTENT = @id_content

            AND a.MATCH_STATUS = 'MATCH'

            AND raw IS NOT NULL

            AND TRIM(raw) != ''
        """,
        {
            "id_content": id_content,
        }
    )

    print(
        "✅ SOLUTION SYNC DONE:",
        id_content,
    )


# ============================================================
# REBUILD ENRICHED ROW
# ============================================================

def rebuild_content_enriched_row(
    id_content: str,
):

    # ========================================================
    # DELETE OLD ROW
    # ========================================================

    query_bq(
        f"""
        DELETE FROM `{TABLE_CONTENT_ENRICHED}`
        WHERE id_content = @id_content
        """,
        {
            "id_content": id_content,
        }
    )

    # ========================================================
    # REINSERT ENRICHED ROW
    # ========================================================

    query_bq(
        f"""
        INSERT INTO `{TABLE_CONTENT_ENRICHED}`

        SELECT

            c.ID_CONTENT AS id_content,

            LOWER(
                COALESCE(
                    c.CONTENT_TYPE,
                    'ANALYSIS'
                )
            ) AS content_type,

            c.ID_PRIMARY_COMPANY AS id_primary_company,

            c.SOURCE_ID AS source_id,

            c.TITLE AS title,

            c.EXCERPT AS excerpt,

            c.CONTENT_BODY AS content_body,

            c.SIGNAL_ANALYTIQUE AS signal_analytique,

            c.MECANIQUE_EXPLIQUEE AS mecanique_expliquee,

            c.ENJEU_STRATEGIQUE AS enjeu_strategique,

            c.POINT_DE_FRICTION AS point_de_friction,

            c.CHIFFRES AS chiffres,

            c.ACTEURS_CITES AS acteurs_cites,

            c.CONCEPTS_LLM AS concepts_llm,

            c.PUBLISHED_AT AS published_at,

            c.CREATED_AT AS created_at,

            c.UPDATED_AT AS updated_at,

            -- ====================================================
            -- TOPICS
            -- ====================================================

            ARRAY(
                SELECT AS STRUCT
                    t.ID_TOPIC AS id_topic,
                    t.LABEL AS label,
                    t.TOPIC_AXIS AS topic_axis

                FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_TOPIC` ct

                JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOPIC` t
                  ON ct.ID_TOPIC = t.ID_TOPIC

                WHERE ct.ID_CONTENT = c.ID_CONTENT
            ) AS topics,

            -- ====================================================
            -- COMPANIES
            -- ====================================================

            ARRAY(
                SELECT AS STRUCT
                    co.ID_COMPANY AS id_company,
                    co.NAME AS name

                FROM `{TABLE_CONTENT_COMPANY}` cc

                JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY` co
                  ON cc.ID_COMPANY = co.ID_COMPANY

                WHERE cc.ID_CONTENT = c.ID_CONTENT
            ) AS companies,

            -- ====================================================
            -- SOLUTIONS
            -- ====================================================

            ARRAY(
                SELECT AS STRUCT
                    s.ID_SOLUTION AS id_solution,
                    s.NAME AS name

                FROM `{TABLE_CONTENT_SOLUTION}` cs

                JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION` s
                  ON cs.ID_SOLUTION = s.ID_SOLUTION

                WHERE cs.ID_CONTENT = c.ID_CONTENT
            ) AS solutions,

            -- ====================================================
            -- CONCEPTS
            -- ====================================================

            ARRAY(
                SELECT AS STRUCT
                    cp.ID_CONCEPT AS id_concept,
                    cpt.LABEL AS label

                FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_CONCEPT` cp

                JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONCEPT` cpt
                  ON cp.ID_CONCEPT = cpt.ID_CONCEPT

                WHERE cp.ID_CONTENT = c.ID_CONTENT
            ) AS concepts,

            -- ====================================================
            -- UNIVERSES
            -- ====================================================

            ARRAY(
                SELECT DISTINCT AS STRUCT
                    u.ID_UNIVERSE AS id_universe,
                    u.LABEL AS label

                FROM `{TABLE_CONTENT_COMPANY}` cc

                JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY_UNIVERSE` cu
                  ON cc.ID_COMPANY = cu.ID_COMPANY

                JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_UNIVERSE` u
                  ON cu.ID_UNIVERSE = u.ID_UNIVERSE

                WHERE cc.ID_CONTENT = c.ID_CONTENT
            ) AS universes

        FROM `{TABLE_CONTENT}` c

        WHERE
            c.ID_CONTENT = @id_content

            AND c.STATUS = 'PUBLISHED'
        """,
        {
            "id_content": id_content,
        }
    )

    print(
        "✅ CONTENT_ENRICHED REBUILT:",
        id_content,
    )


# ============================================================
# FULL AFTER PUBLISH SYNC
# ============================================================

def after_publish_sync(
    id_content: str,
):

    started_at = datetime.now(
        timezone.utc
    )

    print(
        "🚀 AFTER PUBLISH SYNC START:",
        id_content,
    )

    # ========================================================
    # MATCHING
    # ========================================================

    sync_content_companies(
        id_content=id_content,
    )

    sync_content_solutions(
        id_content=id_content,
    )

    # ========================================================
    # ENRICHED
    # ========================================================

    rebuild_content_enriched_row(
        id_content=id_content,
    )

    duration = (
        datetime.now(timezone.utc)
        - started_at
    ).total_seconds()

    print(
        "✅ AFTER PUBLISH SYNC DONE:",
        {
            "id_content": id_content,
            "duration_seconds": duration,
        }
    )
