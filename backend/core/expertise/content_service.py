# backend/core/expertise/content_service.py

from google.cloud import bigquery

from utils.bigquery_utils import get_bigquery_client

from core.expertise.content_mapper import (
    normalize_contents,
)

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

# ============================================================
# TABLE
# ============================================================

TABLE_CONTENT = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_ENRICHED"
)

# ============================================================
# LOAD CONTENTS BY IDS
# ============================================================

def load_contents_by_ids(
    content_ids: list[str],
    language: str = "fr",
):

    if not content_ids:

        return []

    client = get_bigquery_client()

    if language == "en":

        title_sql = (
            "COALESCE(c.TITLE_EN, c.TITLE) "
            "AS title"
        )

        excerpt_sql = (
            "COALESCE(c.EXCERPT_EN, c.EXCERPT) "
            "AS excerpt"
        )

    else:

        title_sql = (
            "c.TITLE AS title"
        )

        excerpt_sql = (
            "c.EXCERPT AS excerpt"
        )

    query = f"""
    WITH requested_contents AS (

        SELECT

            content_id,

            position

        FROM UNNEST(
            @content_ids
        ) AS content_id

        WITH OFFSET AS position

    )

    SELECT

        c.ID_CONTENT AS id,

        c.SOURCE_ID AS source_id,
        c.SOURCE_TITLE AS source_title,
        c.SOURCE_URL AS source_url,

        c.PUBLISHED_AT AS published_at,

        {title_sql},
        {excerpt_sql},

        c.CONTENT_BODY AS content_body,

        c.SIGNAL_ANALYTIQUE
            AS signal_analytique,

        c.MECANIQUE_EXPLIQUEE
            AS mecanique_expliquee,

        c.ENJEU_STRATEGIQUE
            AS enjeu_strategique,

        c.POINT_DE_FRICTION
            AS point_de_friction,

        c.CHIFFRES AS chiffres,

        c.ID_PRIMARY_COMPANY,

        c.COMPANIES AS companies,
        c.SOLUTIONS AS solutions,
        c.TOPICS AS topics,
        c.UNIVERSES AS universes,
        c.CONCEPTS AS concepts

    FROM `{TABLE_CONTENT}` c

    INNER JOIN requested_contents requested

        ON requested.content_id =
            c.ID_CONTENT

    ORDER BY

        requested.position
    """

    job_config = bigquery.QueryJobConfig(

        query_parameters=[

            bigquery.ArrayQueryParameter(
                "content_ids",
                "STRING",
                content_ids,
            ),

        ],

    )

    rows = client.query(
        query,
        job_config=job_config,
    ).result()

    return normalize_contents(
        [
            dict(row)
            for row in rows
        ]
    )
