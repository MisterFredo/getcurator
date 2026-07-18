# backend/core/expertise/content_service.py

from google.cloud import bigquery

from utils.bigquery import get_bigquery_client

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
            "COALESCE(TITLE_EN, TITLE) AS title"
        )

        excerpt_sql = (
            "COALESCE(EXCERPT_EN, EXCERPT) AS excerpt"
        )

    else:

        title_sql = "TITLE AS title"

        excerpt_sql = "EXCERPT AS excerpt"

    query = f"""
    SELECT

        ID_CONTENT AS id,

        SOURCE_ID AS source_id,
        SOURCE_TITLE AS source_title,
        SOURCE_URL AS source_url,

        PUBLISHED_AT AS published_at,

        {title_sql},
        {excerpt_sql},

        CONTENT_BODY AS content_body,

        SIGNAL_ANALYTIQUE AS signal_analytique,
        MECANIQUE_EXPLIQUEE AS mecanique_expliquee,
        ENJEU_STRATEGIQUE AS enjeu_strategique,
        POINT_DE_FRICTION AS point_de_friction,

        CHIFFRES AS chiffres,

        ID_PRIMARY_COMPANY,

        COMPANIES AS companies,
        SOLUTIONS AS solutions,
        TOPICS AS topics,
        UNIVERSES AS universes,
        CONCEPTS AS concepts

    FROM `{TABLE_CONTENT}`

    WHERE
        ID_CONTENT IN UNNEST(@content_ids)
    """

    job_config = bigquery.QueryJobConfig(

        query_parameters=[

            bigquery.ArrayQueryParameter(
                "content_ids",
                "STRING",
                content_ids,
            )

        ]

    )

    rows = client.query(
        query,
        job_config=job_config,
    ).result()

    return normalize_contents(
        [dict(row) for row in rows]
    )
