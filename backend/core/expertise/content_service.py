# backend/core/expertise/content_service.py

from google.cloud import bigquery

from api.expertise.models import ExpertiseContent

from core.bigquery import get_bigquery_client
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
) -> list[ExpertiseContent]:

    if not content_ids:
        return []

    client = get_bigquery_client()

    if language == "en":

        title_sql = (
            "COALESCE(TITLE_EN, TITLE) AS TITLE"
        )

        excerpt_sql = (
            "COALESCE(EXCERPT_EN, EXCERPT) AS EXCERPT"
        )

    else:

        title_sql = "TITLE"

        excerpt_sql = "EXCERPT"

    query = f"""
    SELECT

        ID_CONTENT,

        {title_sql},
        {excerpt_sql},

        CONTENT_BODY,

        SIGNAL_ANALYTIQUE,
        MECANIQUE_EXPLIQUEE,
        ENJEU_STRATEGIQUE,
        POINT_DE_FRICTION,

        CHIFFRES,

        SOURCE_TITLE,
        SOURCE_URL,
        SOURCE_DATE,
        PUBLISHED_AT,

        COMPANIES,
        SOLUTIONS,
        TOPICS,
        CONCEPTS

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

    contents = []

    for row in rows:

        contents.append(

            ExpertiseContent(

                id_content=row.ID_CONTENT,

                title=row.TITLE,
                excerpt=row.EXCERPT,

                content_body=row.CONTENT_BODY,

                signal_analytique=row.SIGNAL_ANALYTIQUE,
                mecanique_expliquee=row.MECANIQUE_EXPLIQUEE,
                enjeu_strategique=row.ENJEU_STRATEGIQUE,
                point_de_friction=row.POINT_DE_FRICTION,

                chiffres=row.CHIFFRES,

                source_title=row.SOURCE_TITLE,
                source_url=row.SOURCE_URL,
                source_date=row.SOURCE_DATE,
                published_at=row.PUBLISHED_AT,

                companies=row.COMPANIES or [],
                solutions=row.SOLUTIONS or [],
                topics=row.TOPICS or [],
                concepts=row.CONCEPTS or [],

            )

        )

    return contents
