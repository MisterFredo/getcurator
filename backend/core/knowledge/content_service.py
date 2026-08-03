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
# TABLES
# ============================================================

TABLE_CONTENT = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_ENRICHED"
)

TABLE_CONTENT_COMPANY = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_COMPANY"
)

TABLE_CONTENT_TOPIC = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_TOPIC"
)

TABLE_CONTENT_SOLUTION = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_SOLUTION"
)


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

    match entity_type:

        case "company":
            return _load_contents(
                relation_table=TABLE_CONTENT_COMPANY,
                relation_column="ID_COMPANY",
                entity_id=entity_id,
                block_type=block_type,
            )

        case "topic":
            return _load_contents(
                relation_table=TABLE_CONTENT_TOPIC,
                relation_column="ID_TOPIC",
                entity_id=entity_id,
                block_type=block_type,
            )

        case "solution":
            return _load_contents(
                relation_table=TABLE_CONTENT_SOLUTION,
                relation_column="ID_SOLUTION",
                entity_id=entity_id,
                block_type=block_type,
            )

    return []


# ============================================================
# GENERIC LOADER
# ============================================================

def _load_contents(
    relation_table: str,
    relation_column: str,
    entity_id: str,
    block_type: KnowledgeBlockType,
) -> list[KnowledgeObservation]:

    column = BLOCK_COLUMNS[
        block_type
    ]

    column = block_columns[
        block_type
    ]

    query = f"""
    SELECT

        c.ID_CONTENT,

        c.TITLE,

        c.EXCERPT,

        c.{column} AS CONTENT,

        c.PUBLISHED_AT

    FROM `{TABLE_CONTENT}` c

    JOIN `{relation_table}` r

        ON r.ID_CONTENT = c.ID_CONTENT

    WHERE

        r.{relation_column} = @entity_id

    AND

        c.STATUS = "PUBLISHED"

    AND

        c.IS_ACTIVE = TRUE

    AND

        c.PUBLISHED_AT IS NOT NULL

    ORDER BY

        c.PUBLISHED_AT ASC
    """

    rows = query_bq(
        query,
        {
            "entity_id": entity_id,
        },
    ) or []

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
# LOAD NEW CONTENTS
# ============================================================

def load_new_contents(
    entity_type: KnowledgeEntityType,
    entity_id: str,
    block_type: KnowledgeBlockType,
    last_content_date,
) -> list[KnowledgeObservation]:
    """
    Load only the contents published after
    the last Knowledge update.

    Used by the incremental update engine.
    """

    match entity_type:

        case "company":
            return _load_new_contents(
                relation_table=TABLE_CONTENT_COMPANY,
                relation_column="ID_COMPANY",
                entity_id=entity_id,
                block_type=block_type,
                last_content_date=last_content_date,
            )

        case "topic":
            return _load_new_contents(
                relation_table=TABLE_CONTENT_TOPIC,
                relation_column="ID_TOPIC",
                entity_id=entity_id,
                block_type=block_type,
                last_content_date=last_content_date,
            )

        case "solution":
            return _load_new_contents(
                relation_table=TABLE_CONTENT_SOLUTION,
                relation_column="ID_SOLUTION",
                entity_id=entity_id,
                block_type=block_type,
                last_content_date=last_content_date,
            )

    return []
# ============================================================
# GENERIC UPDATE LOADER
# ============================================================

def _load_new_contents(
    relation_table: str,
    relation_column: str,
    entity_id: str,
    block_type: KnowledgeBlockType,
    last_content_date,
) -> list[KnowledgeObservation]:
    """
    Load only contents newer than the last
    processed content.
    """

    column = BLOCK_COLUMNS[
        block_type
    ]

    query = f"""
    SELECT DISTINCT

        c.ID_CONTENT,

        c.TITLE,

        c.EXCERPT,

        c.{column} AS CONTENT,

        c.PUBLISHED_AT

    FROM `{TABLE_CONTENT}` c

    JOIN `{relation_table}` r

        ON r.ID_CONTENT = c.ID_CONTENT

    WHERE

        r.{relation_column} = @entity_id

    AND

        c.STATUS = "PUBLISHED"

    AND

        c.IS_ACTIVE = TRUE

    AND

        c.PUBLISHED_AT IS NOT NULL

    AND

        c.PUBLISHED_AT > @last_content_date

    ORDER BY

        c.PUBLISHED_AT ASC
    """

    rows = query_bq(
        query,
        {
            "entity_id": entity_id,
            "last_content_date": last_content_date,
        },
    ) or []

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
    batch_size: int = 50,
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
