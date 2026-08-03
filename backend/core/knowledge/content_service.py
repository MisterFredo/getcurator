# backend/core/knowledge/content_service.py

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
)

from .models import (
    KnowledgeContent,
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
# LOAD CONTENTS
# ============================================================

def load_contents(
    entity_type: KnowledgeEntityType,
    entity_id: str,
) -> list[KnowledgeContent]:

    match entity_type:

        case "company":
            return _load_contents(
                relation_table=TABLE_CONTENT_COMPANY,
                relation_column="ID_COMPANY",
                entity_id=entity_id,
            )

        case "topic":
            return _load_contents(
                relation_table=TABLE_CONTENT_TOPIC,
                relation_column="ID_TOPIC",
                entity_id=entity_id,
            )

        case "solution":
            return _load_contents(
                relation_table=TABLE_CONTENT_SOLUTION,
                relation_column="ID_SOLUTION",
                entity_id=entity_id,
            )

    return []


# ============================================================
# GENERIC LOADER
# ============================================================

def _load_contents(
    relation_table: str,
    relation_column: str,
    entity_id: str,
) -> list[KnowledgeContent]:

    query = f"""
    SELECT

        c.ID_CONTENT,

        c.TITLE,

        c.EXCERPT,

        c.SIGNAL_ANALYTIQUE,

        c.MECANIQUE_EXPLIQUEE,

        c.ENJEU_STRATEGIQUE,

        c.POINT_DE_FRICTION,

        c.CHIFFRES,

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

        KnowledgeContent(

            id=row["ID_CONTENT"],

            title=row["TITLE"],

            excerpt=row["EXCERPT"],

            signal_analytique=row.get("SIGNAL_ANALYTIQUE") or "",

            mecanique_expliquee=row.get("MECANIQUE_EXPLIQUEE") or "",

            enjeu_strategique=row.get("ENJEU_STRATEGIQUE") or "",

            point_de_friction=row.get("POINT_DE_FRICTION") or "",

            chiffres=row.get("CHIFFRES") or "",

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
    last_content_date,
) -> list[KnowledgeContent]:
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
                last_content_date=last_content_date,
            )

        case "topic":
            return _load_new_contents(
                relation_table=TABLE_CONTENT_TOPIC,
                relation_column="ID_TOPIC",
                entity_id=entity_id,
                last_content_date=last_content_date,
            )

        case "solution":
            return _load_new_contents(
                relation_table=TABLE_CONTENT_SOLUTION,
                relation_column="ID_SOLUTION",
                entity_id=entity_id,
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
    last_content_date,
) -> list[KnowledgeContent]:
    """
    Load only contents newer than the last
    processed content.
    """

    query = f"""
    SELECT DISTINCT

        c.ID_CONTENT,

        c.TITLE,

        c.EXCERPT,

        c.SIGNAL_ANALYTIQUE,

        c.MECANIQUE_EXPLIQUEE,

        c.ENJEU_STRATEGIQUE,

        c.POINT_DE_FRICTION,

        c.CHIFFRES,

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

        KnowledgeContent(

            id=row["ID_CONTENT"],

            title=row["TITLE"],

            excerpt=row["EXCERPT"],

            signal_analytique=row.get("SIGNAL_ANALYTIQUE") or "",

            mecanique_expliquee=row.get("MECANIQUE_EXPLIQUEE") or "",

            enjeu_strategique=row.get("ENJEU_STRATEGIQUE") or "",

            point_de_friction=row.get("POINT_DE_FRICTION") or "",

            chiffres=row.get("CHIFFRES") or "",

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
    batch_size: int = 50,
) -> list[list[KnowledgeContent]]:
    """
    Load contents and split them into
    chronological batches.
    """

    contents = load_contents(
        entity_type=entity_type,
        entity_id=entity_id,
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
