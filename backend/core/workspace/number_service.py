# backend/core/workspace/number_service.py

from google.cloud import bigquery

from api.workspace.models import (
    WorkspaceNumber,
)

from core.bigquery import get_bigquery_client

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

# ============================================================
# TABLE
# ============================================================

TABLE_NUMBERS = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS"
)

# ============================================================
# LOAD NUMBERS BY IDS
# ============================================================

def load_numbers_by_ids(
    number_ids: list[str],
) -> list[WorkspaceNumber]:

    if not number_ids:
        return []

    client = get_bigquery_client()

    query = f"""
    SELECT

        ID_NUMBER,

        LABEL,
        VALUE,
        UNIT,
        SCALE,

        TYPE,
        CATEGORY,

        ZONE,
        PERIOD,

        ENTITY_LABEL

    FROM `{TABLE_NUMBERS}`

    WHERE
        ID_NUMBER IN UNNEST(@number_ids)
    """

    job_config = bigquery.QueryJobConfig(

        query_parameters=[

            bigquery.ArrayQueryParameter(
                "number_ids",
                "STRING",
                number_ids,
            )

        ]

    )

    rows = client.query(
        query,
        job_config=job_config,
    ).result()

    numbers: list[WorkspaceNumber] = []

    for row in rows:

        numbers.append(

            WorkspaceNumber(

                id_number=row.ID_NUMBER,

                label=row.LABEL,

                value=row.VALUE,
                unit=row.UNIT,
                scale=row.SCALE,

                type=row.TYPE,
                category=row.CATEGORY,

                zone=row.ZONE,
                period=row.PERIOD,

                entity_label=row.ENTITY_LABEL,

            )

        )

    return numbers
