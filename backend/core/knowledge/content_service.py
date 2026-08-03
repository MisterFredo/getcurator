# backend/core/knowledge/content_service.py

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
)

from .models import (
    KnowledgeObservation,
    KnowledgeBlockType,
    KnowledgeEntityType,
)


# ============================================================
# TABLE
# ============================================================

TABLE_CONTENT = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_ENRICHED"
)

# ============================================================
# CONFIG
# ============================================================

KNOWLEDGE_BATCH_SIZE = 50
KNOWLEDGE_BUILD_OFFSET = 0
KNOWLEDGE_BUILD_LIMIT = 50


# ============================================================
# ENTITY CONFIG
# ============================================================

ENTITY_CONFIG = {

    "company": {

        "array": "COMPANIES",

        "id_field": "id_company",

    },

    "topic": {

        "array": "TOPICS",

        "id_field": "id_topic",

    },

    "solution": {

        "array": "SOLUTIONS",

        "id_field": "id_solution",

    },

}


# ============================================================
# BLOCK COLUMNS
# ============================================================

BLOCK_COLUMNS = {

    "signal_analytique":
        "SIGNAL_ANALYTIQUE",

    "mecanique_expliquee":
        "MECANIQUE_EXPLIQUEE",

    "enjeu_strategique":
        "ENJEU_STRATEGIQUE",

    "point_de_friction":
        "POINT_DE_FRICTION",

    "chiffres":
        "CHIFFRES",

}


# ============================================================
# LOAD CONTENTS
# ============================================================

def load_contents(
    entity_type: KnowledgeEntityType,
    entity_id: str,
    block_type: KnowledgeBlockType,
) -> list[KnowledgeObservation]:
    return _load_contents(
        entity_type=entity_type,
        entity_id=entity_id,
        block_type=block_type,
    )


def load_new_contents(
    entity_type: KnowledgeEntityType,
    entity_id: str,
    block_type: KnowledgeBlockType,
    last_content_date,
) -> list[KnowledgeObservation]:

    return _load_contents(

        entity_type=entity_type,

        entity_id=entity_id,

        block_type=block_type,

        last_content_date=last_content_date,

    )

# ============================================================
# GENERIC LOADER
# ============================================================

def _load_contents(
    entity_type: KnowledgeEntityType,
    entity_id: str,
    block_type: KnowledgeBlockType,
    last_content_date=None,
) -> list[KnowledgeObservation]:

    config = ENTITY_CONFIG[
        entity_type
    ]

    entity_array = config[
        "array"
    ]

    id_field = config[
        "id_field"
    ]

    column = BLOCK_COLUMNS[
        block_type
    ]

    date_filter = ""

    params = {
        "entity_id": entity_id,
    }

    if last_content_date:

        date_filter = """
        AND c.PUBLISHED_AT > @last_content_date
        """

        params["last_content_date"] = (
            last_content_date
        )

    query = f"""
    SELECT

        c.ID_CONTENT,

        c.TITLE,

        c.EXCERPT,

        c.{column} AS CONTENT,

        c.PUBLISHED_AT

    FROM `{TABLE_CONTENT}` c

    CROSS JOIN UNNEST(
        c.{entity_array}
    ) AS entity

    WHERE

        entity.{id_field} = @entity_id

    AND

        c.STATUS = "PUBLISHED"

    AND

        c.IS_ACTIVE = TRUE

    AND

        c.PUBLISHED_AT IS NOT NULL

    {date_filter}

    ORDER BY

        c.PUBLISHED_AT ASC
    """

    rows = query_bq(
        query,
        params,
    ) or []

    # ========================================================
    # V1 LIMIT
    # ========================================================

    if KNOWLEDGE_BUILD_LIMIT is not None:

        rows = rows[
            KNOWLEDGE_BUILD_OFFSET:
            KNOWLEDGE_BUILD_OFFSET + KNOWLEDGE_BUILD_LIMIT
        ]

    return [

        KnowledgeObservation(

            id=row["ID_CONTENT"],

            title=row["TITLE"],

            excerpt=row["EXCERPT"],

            content=row.get("CONTENT") or "",

            published_at=row["PUBLISHED_AT"],

        )

        for row in rows

    ]

# ============================================================
# LOAD BATCHES
# ============================================================

def load_batches(
    entity_type: KnowledgeEntityType,
    entity_id: str,
    block_type: KnowledgeBlockType,
    batch_size: int = KNOWLEDGE_BATCH_SIZE,
) -> list[list[KnowledgeObservation]]:
    """
    Load contents and split them into
    chronological batches.
    """

    contents = load_contents(
        entity_type=entity_type,
        entity_id=entity_id,
        block_type=block_type,
    )

    if not contents:
        return []

    return [

        contents[i:i + batch_size]

        for i in range(
            0,
            len(contents),
            batch_size,
        )

    ]
