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

TABLE_CONTENT_ENRICHED = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_ENRICHED"
)

TABLE_CONTENT_TOPIC = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_TOPIC"
)

TABLE_CONTENT_COMPANY = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_COMPANY"
)

TABLE_CONTENT_SOLUTION = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_SOLUTION"
)

TABLE_CONTENT_CONCEPT = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_CONCEPT"
)

TABLE_SOURCE_UNIVERSE = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOURCE_UNIVERSE"
)

TABLE_UNIVERSE = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_UNIVERSE"
)

TABLE_TOPIC = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOPIC"
)

TABLE_COMPANY = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY"
)

TABLE_SOLUTION = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION"
)

TABLE_CONCEPT = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONCEPT"
)

# ============================================================
# BUILD ENRICHED ROW
# ============================================================

def build_content_enriched_row(
    id_content: str,
):

    query_bq(
        f"""
        DELETE FROM `{TABLE_CONTENT_ENRICHED}`
        WHERE id_content = @id_content
        """,
        {
            "id_content": id_content,
        }
    )

    query_bq(
        f"""
        INSERT INTO `{TABLE_CONTENT_ENRICHED}` (
            id_content,
            source_id,
            title,
            title_en,
            excerpt,
            excerpt_en,
            content_body,
            signal_analytique,
            mecanique_expliquee,
            enjeu_strategique,
            point_de_friction,
            chiffres,
            acteurs_cites,
            concepts_llm,
            solutions_llm,
            topics_llm,
            status,
            is_active,
            source_date,
            published_at,
            created_at,
            updated_at,
            universes,
            topics,
            companies,
            solutions,
            concepts,
            id_primary_company
        )

        SELECT
            c.ID_CONTENT AS id_content,
            c.SOURCE_ID AS source_id,
            c.TITLE AS title,
            c.TITLE_EN AS title_en,
            c.EXCERPT AS excerpt,
            c.EXCERPT_EN AS excerpt_en,
            c.CONTENT_BODY AS content_body,
            c.SIGNAL_ANALYTIQUE AS signal_analytique,
            c.MECANIQUE_EXPLIQUEE AS mecanique_expliquee,
            c.ENJEU_STRATEGIQUE AS enjeu_strategique,
            c.POINT_DE_FRICTION AS point_de_friction,
            c.CHIFFRES AS chiffres,
            c.ACTEURS_CITES AS acteurs_cites,
            c.CONCEPTS_LLM AS concepts_llm,
            c.SOLUTIONS_LLM AS solutions_llm,
            c.TOPICS_LLM AS topics_llm,
            c.STATUS AS status,
            c.IS_ACTIVE AS is_active,
            c.SOURCE_DATE AS source_date,
            c.PUBLISHED_AT AS published_at,
            c.CREATED_AT AS created_at,
            c.UPDATED_AT AS updated_at,

            ARRAY(
                SELECT DISTINCT AS STRUCT
                    u.ID_UNIVERSE AS id_universe,
                    u.LABEL AS label

                FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOURCE_UNIVERSE` su

                JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_UNIVERSE` u
                    ON su.ID_UNIVERSE = u.ID_UNIVERSE

                WHERE su.ID_SOURCE = c.SOURCE_ID
            ) AS universes,

            ARRAY(
                SELECT DISTINCT AS STRUCT
                    t.ID_TOPIC AS id_topic,
                    t.LABEL AS label,
                    t.TOPIC_AXIS AS topic_axis

                FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_TOPIC` ct

                JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOPIC` t
                    ON ct.ID_TOPIC = t.ID_TOPIC

                WHERE ct.ID_CONTENT = c.ID_CONTENT
            ) AS topics,

            ARRAY(
                SELECT DISTINCT AS STRUCT
                    co.ID_COMPANY AS id_company,
                    co.NAME AS name,
                    co.MEDIA_LOGO_RECTANGLE_ID AS media_logo_rectangle_id

                FROM `{TABLE_CONTENT_COMPANY}` cc

                JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY` co
                    ON cc.ID_COMPANY = co.ID_COMPANY

                WHERE cc.ID_CONTENT = c.ID_CONTENT
            ) AS companies,

            ARRAY(
                SELECT DISTINCT AS STRUCT
                    s.ID_SOLUTION AS id_solution,
                    s.NAME AS name

                FROM `{TABLE_CONTENT_SOLUTION}` cs

                JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION` s
                    ON cs.ID_SOLUTION = s.ID_SOLUTION

                WHERE cs.ID_CONTENT = c.ID_CONTENT
            ) AS solutions,

            ARRAY(
                SELECT DISTINCT AS STRUCT
                    cp.ID_CONCEPT AS id_concept,
                    cpt.LABEL AS label

                FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_CONCEPT` cp

                JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONCEPT` cpt
                    ON cp.ID_CONCEPT = cpt.ID_CONCEPT

                WHERE cp.ID_CONTENT = c.ID_CONTENT
            ) AS concepts,

            c.ID_PRIMARY_COMPANY AS id_primary_company

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
