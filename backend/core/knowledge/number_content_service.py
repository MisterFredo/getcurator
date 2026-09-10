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
    KnowledgeNumberObservation,
)


# ============================================================
# TABLES
# ============================================================

TABLE_NUMBER = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_NUMBER_OBSERVATION"
)

TABLE_NUMBER_ENTITY = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_NUMBER_OBSERVATION_ENTITY"
)

TABLE_CONTENT = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_CONTENT_ENRICHED"
)


# ============================================================
# CONFIG
# ============================================================

KNOWLEDGE_NUMBER_BATCH_SIZE = 50
KNOWLEDGE_NUMBER_BUILD_LIMIT = 50


# ============================================================
# LOAD NUMBER OBSERVATIONS
# ============================================================

def load_number_observations(
    entity_type: KnowledgeEntityType,
    entity_id: str,
    last_published_at: datetime | None = None,
    limit: int = KNOWLEDGE_NUMBER_BUILD_LIMIT,
) -> list[KnowledgeNumberObservation]:
    """
    Load validated Numbers associated with
    one official GetCurator entity.
    """

    date_filter = ""

    params = {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "limit": limit,
    }

    if last_published_at:

        date_filter = """
        AND n.PUBLISHED_AT > @last_published_at
        """

        params["last_published_at"] = (
            last_published_at
        )

    rows = query_bq(
        f"""
        SELECT

            n.ID_NUMBER,

            n.ID_CONTENT,

            c.TITLE,

            n.LABEL,

            n.METRIC_TYPE,

            n.VALUE,

            n.VALUE_MIN,

            n.VALUE_MAX,

            n.UNIT,

            n.SCALE,

            n.ZONE,

            n.PERIOD_LABEL,

            n.VALUE_STATUS,

            n.RAW_LINE,

            n.CONFIDENCE,

            n.PUBLISHED_AT

        FROM `{TABLE_NUMBER}` n

        JOIN `{TABLE_NUMBER_ENTITY}` ne
          ON ne.ID_NUMBER = n.ID_NUMBER

        LEFT JOIN `{TABLE_CONTENT}` c
          ON c.ID_CONTENT = n.ID_CONTENT

        WHERE n.STATUS = 'ACCEPTED'

          AND ne.ENTITY_TYPE = @entity_type

          AND ne.ENTITY_ID = @entity_id

          AND n.PUBLISHED_AT IS NOT NULL

          {date_filter}

        ORDER BY
          n.PUBLISHED_AT ASC,
          n.ID_NUMBER ASC

        LIMIT @limit
        """,
        params,
    ) or []

    return [
        KnowledgeNumberObservation(

            id_number=row["ID_NUMBER"],

            id_content=row["ID_CONTENT"],

            title=(
                row.get("TITLE")
                or "Untitled content"
            ),

            label=row["LABEL"],

            metric_type=row["METRIC_TYPE"],

            value=row.get("VALUE"),

            value_min=row.get("VALUE_MIN"),

            value_max=row.get("VALUE_MAX"),

            unit=row["UNIT"],

            scale=row["SCALE"],

            zone=row["ZONE"],

            period_label=row["PERIOD_LABEL"],

            value_status=row["VALUE_STATUS"],

            raw_line=row["RAW_LINE"],

            confidence=(
                row.get("CONFIDENCE")
                or 0.0
            ),

            published_at=row["PUBLISHED_AT"],

        )

        for row in rows
    ]


# ============================================================
# LOAD NUMBER BATCHES
# ============================================================

def load_number_batches(
    entity_type: KnowledgeEntityType,
    entity_id: str,
    last_published_at: datetime | None = None,
    limit: int = KNOWLEDGE_NUMBER_BUILD_LIMIT,
    batch_size: int = KNOWLEDGE_NUMBER_BATCH_SIZE,
) -> list[list[KnowledgeNumberObservation]]:
    """
    Load accepted Number observations and split
    them into chronological batches.
    """

    observations = load_number_observations(

        entity_type=entity_type,

        entity_id=entity_id,

        last_published_at=last_published_at,

        limit=limit,

    )

    if not observations:
        return []

    return [

        observations[
            i:i + batch_size
        ]

        for i in range(
            0,
            len(observations),
            batch_size,
        )
    ]
