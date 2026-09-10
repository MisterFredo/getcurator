from datetime import datetime

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
)

from .models import (
    KnowledgeEntityType,
)


# ============================================================
# TABLE
# ============================================================

TABLE_NUMBER_STATUS = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_KNOWLEDGE_NUMBER_STATUS"
)


# ============================================================
# GET CURSOR
# ============================================================

def get_number_knowledge_cursor(
    entity_type: KnowledgeEntityType,
    entity_id: str,
) -> tuple[
    datetime | None,
    str | None,
]:

    rows = query_bq(
        f"""
        SELECT
          LAST_PUBLISHED_AT,
          LAST_NUMBER_ID

        FROM `{TABLE_NUMBER_STATUS}`

        WHERE ENTITY_TYPE = @entity_type
          AND ENTITY_ID = @entity_id

        LIMIT 1
        """,
        {
            "entity_type": entity_type,
            "entity_id": entity_id,
        },
    ) or []

    if not rows:

        return (
            None,
            None,
        )

    return (
        rows[0].get(
            "LAST_PUBLISHED_AT"
        ),
        rows[0].get(
            "LAST_NUMBER_ID"
        ),
    )


# ============================================================
# UPDATE CURSOR
# ============================================================

def update_number_knowledge_cursor(
    entity_type: KnowledgeEntityType,
    entity_id: str,
    last_published_at: datetime,
    last_number_id: str,
    processed_count: int,
):

    query_bq(
        f"""
        MERGE `{TABLE_NUMBER_STATUS}` target

        USING (
          SELECT
            @entity_type AS ENTITY_TYPE,
            @entity_id AS ENTITY_ID
        ) source

        ON target.ENTITY_TYPE = source.ENTITY_TYPE
       AND target.ENTITY_ID = source.ENTITY_ID

        WHEN MATCHED THEN
          UPDATE SET
            LAST_PUBLISHED_AT = @last_published_at,
            LAST_NUMBER_ID = @last_number_id,
            PROCESSED_OBSERVATIONS = (
              COALESCE(
                target.PROCESSED_OBSERVATIONS,
                0
              ) + @processed_count
            ),
            UPDATED_AT = CURRENT_TIMESTAMP()

        WHEN NOT MATCHED THEN
          INSERT (
            ENTITY_TYPE,
            ENTITY_ID,
            LAST_PUBLISHED_AT,
            LAST_NUMBER_ID,
            PROCESSED_OBSERVATIONS,
            CREATED_AT,
            UPDATED_AT
          )
          VALUES (
            @entity_type,
            @entity_id,
            @last_published_at,
            @last_number_id,
            @processed_count,
            CURRENT_TIMESTAMP(),
            CURRENT_TIMESTAMP()
          )
        """,
        {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "last_published_at": (
                last_published_at
            ),
            "last_number_id": (
                last_number_id
            ),
            "processed_count": (
                processed_count
            ),
        },
    )
