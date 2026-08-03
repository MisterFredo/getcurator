# backend/core/knowledge/repository.py

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
)

from .models import (
    KnowledgeBlock,
    KnowledgeBlockType,
    KnowledgeEntity,
    KnowledgeEntityType,
)


# ============================================================
# TABLE
# ============================================================

TABLE_KNOWLEDGE = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_KNOWLEDGE"
)


# ============================================================
# UPSERT BLOCK
# ============================================================

def upsert_block(
    entity_type: KnowledgeEntityType,
    entity_id: str,
    block: KnowledgeBlock,
):
    """
    Insert or update one Knowledge Block.
    """

    query = f"""
    MERGE `{TABLE_KNOWLEDGE}` T

    USING (

        SELECT

            @entity_type AS ENTITY_TYPE,

            @entity_id AS ENTITY_ID,

            @block_type AS BLOCK_TYPE,

            @content AS CONTENT,

            @version AS VERSION

    ) S

    ON

        T.ENTITY_TYPE = S.ENTITY_TYPE

    AND

        T.ENTITY_ID = S.ENTITY_ID

    AND

        T.BLOCK_TYPE = S.BLOCK_TYPE

    WHEN MATCHED THEN

        UPDATE SET

            CONTENT = S.CONTENT,

            VERSION = S.VERSION,

            UPDATED_AT = CURRENT_TIMESTAMP()

    WHEN NOT MATCHED THEN

        INSERT (

            ENTITY_TYPE,

            ENTITY_ID,

            BLOCK_TYPE,

            CONTENT,

            VERSION,

            UPDATED_AT

        )

        VALUES (

            S.ENTITY_TYPE,

            S.ENTITY_ID,

            S.BLOCK_TYPE,

            S.CONTENT,

            S.VERSION,

            CURRENT_TIMESTAMP()

        )
    """

    query_bq(
        query,
        {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "block_type": block.block_type,
            "content": block.content,
            "version": block.version,
        },
    )


# ============================================================
# GET BLOCK
# ============================================================

def get_block(
    entity_type: KnowledgeEntityType,
    entity_id: str,
    block_type: KnowledgeBlockType,
):

    rows = query_bq(
        f"""
        SELECT

            BLOCK_TYPE,

            CONTENT,

            VERSION,

            UPDATED_AT

        FROM `{TABLE_KNOWLEDGE}`

        WHERE

            ENTITY_TYPE = @entity_type

        AND

            ENTITY_ID = @entity_id

        AND

            BLOCK_TYPE = @block_type

        """,
        {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "block_type": block_type,
        },
    )

    if not rows:
        return None

    row = rows[0]

    return KnowledgeBlock(
        block_type=row["BLOCK_TYPE"],
        content=row.get("CONTENT") or "",
        version=row.get("VERSION", 1),
        updated_at=row["UPDATED_AT"],
    )


# ============================================================
# GET ENTITY
# ============================================================

def get_entity(
    entity_type: KnowledgeEntityType,
    entity_id: str,
):

    rows = query_bq(
        f"""
        SELECT

            BLOCK_TYPE,

            CONTENT,

            VERSION,

            UPDATED_AT

        FROM `{TABLE_KNOWLEDGE}`

        WHERE

            ENTITY_TYPE = @entity_type

        AND

            ENTITY_ID = @entity_id
        """,
        {
            "entity_type": entity_type,
            "entity_id": entity_id,
        },
    )

    if not rows:
        return None

    blocks = {}

    updated_at = None

    for row in rows:

        block = KnowledgeBlock(
            block_type=row["BLOCK_TYPE"],
            content=row.get("CONTENT") or "",
            version=row.get("VERSION", 1),
            updated_at=row["UPDATED_AT"],
        )

        blocks[block.block_type] = block

        updated_at = max(
            updated_at,
            block.updated_at,
        ) if updated_at else block.updated_at

    return KnowledgeEntity(

        entity_type=entity_type,

        entity_id=entity_id,

        signal_analytique=blocks["signal_analytique"],

        mecanique_expliquee=blocks["mecanique_expliquee"],

        enjeu_strategique=blocks["enjeu_strategique"],

        point_de_friction=blocks["point_de_friction"],

        chiffres=blocks["chiffres"],

        updated_at=updated_at,

    )


# ============================================================
# DELETE ENTITY
# ============================================================

def delete_entity(
    entity_type: KnowledgeEntityType,
    entity_id: str,
):
    """
    Delete every block attached to one entity.
    """

    query_bq(
        f"""
        DELETE
        FROM `{TABLE_KNOWLEDGE}`

        WHERE

            ENTITY_TYPE = @entity_type

        AND

            ENTITY_ID = @entity_id
        """,
        {
            "entity_type": entity_type,
            "entity_id": entity_id,
        },
    )
