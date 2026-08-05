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

TABLE_KNOWLEDGE_STATUS = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_KNOWLEDGE_STATUS"
)

# ============================================================
# UPSERT BLOCK
# ============================================================

def upsert_block(
    entity_type: KnowledgeEntityType,
    entity_id: str,
    block: KnowledgeBlock,
    updated_by: str = "LLM",
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

            @version AS VERSION,

            @updated_by AS UPDATED_BY

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

            UPDATED_AT = CURRENT_TIMESTAMP(),

            UPDATED_BY = S.UPDATED_BY

    WHEN NOT MATCHED THEN

        INSERT (

            ENTITY_TYPE,

            ENTITY_ID,

            BLOCK_TYPE,

            CONTENT,

            VERSION,

            UPDATED_AT,

            UPDATED_BY

        )

        VALUES (

            S.ENTITY_TYPE,

            S.ENTITY_ID,

            S.BLOCK_TYPE,

            S.CONTENT,

            S.VERSION,

            CURRENT_TIMESTAMP(),

            S.UPDATED_BY

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
            "updated_by": updated_by,
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
# EMPTY BLOCK
# ============================================================

def _empty_block(
    block_type: KnowledgeBlockType,
) -> KnowledgeBlock:

    from datetime import (
        datetime,
        timezone,
    )

    return KnowledgeBlock(

        block_type=block_type,

        content="",

        version=0,

        updated_at=datetime.now(
            timezone.utc,
        ),

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

        return KnowledgeEntity(
    
            entity_type=entity_type,
    
            entity_id=entity_id,
    
            name="",
    
            signal_analytique=_empty_block(
                "signal_analytique",
            ),
    
            mecanique_expliquee=_empty_block(
                "mecanique_expliquee",
            ),
    
            enjeu_strategique=_empty_block(
                "enjeu_strategique",
            ),
    
            point_de_friction=_empty_block(
                "point_de_friction",
            ),
    
            chiffres=_empty_block(
                "chiffres",
            ),
    
            updated_at=None,
    
        )

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

        signal_analytique=blocks.get(
            "signal_analytique",
            _empty_block("signal_analytique"),
        ),

        mecanique_expliquee=blocks.get(
            "mecanique_expliquee",
            _empty_block("mecanique_expliquee"),
        ),

        enjeu_strategique=blocks.get(
            "enjeu_strategique",
            _empty_block("enjeu_strategique"),
        ),
    
        point_de_friction=blocks.get(
            "point_de_friction",
            _empty_block("point_de_friction"),
        ),
    
        chiffres=blocks.get(
            "chiffres",
            _empty_block("chiffres"),
        ),
    
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

# ============================================================
# EXISTS
# ============================================================

def exists_entity(
    entity_type: KnowledgeEntityType,
    entity_id: str,
) -> bool:

    rows = query_bq(
        f"""
        SELECT 1

        FROM `{TABLE_KNOWLEDGE}`

        WHERE

            ENTITY_TYPE = @entity_type

        AND

            ENTITY_ID = @entity_id

        LIMIT 1
        """,
        {
            "entity_type": entity_type,
            "entity_id": entity_id,
        },
    )

    return bool(rows)

# ============================================================
# GET STATUS
# ============================================================

def get_last_content_date(
    entity_type: KnowledgeEntityType,
    entity_id: str,
):

    rows = query_bq(

        f"""
        SELECT

            LAST_CONTENT_DATE

        FROM `{TABLE_KNOWLEDGE_STATUS}`

        WHERE

            ENTITY_TYPE = @entity_type

        AND

            ENTITY_ID = @entity_id

        LIMIT 1
        """,

        {
            "entity_type": entity_type,
            "entity_id": entity_id,
        },

    )

    if not rows:

        return None

    return rows[0].get(
        "LAST_CONTENT_DATE",
    )

# ============================================================
# UPDATE STATUS
# ============================================================

def update_last_content(
    entity_type: KnowledgeEntityType,
    entity_id: str,
    content_id: str,
    content_date,
):
    """
    Update the last processed content
    for one Knowledge entity.
    """

    query = f"""
    MERGE `{TABLE_KNOWLEDGE_STATUS}` T

    USING (

        SELECT

            @entity_type AS ENTITY_TYPE,

            @entity_id AS ENTITY_ID,

            @content_id AS LAST_CONTENT_ID,

            @content_date AS LAST_CONTENT_DATE

    ) S

    ON

        T.ENTITY_TYPE = S.ENTITY_TYPE

    AND

        T.ENTITY_ID = S.ENTITY_ID

    WHEN MATCHED THEN

        UPDATE SET

            LAST_CONTENT_ID = S.LAST_CONTENT_ID,

            LAST_CONTENT_DATE = S.LAST_CONTENT_DATE,

            KNOWLEDGE_VERSION = COALESCE(
                T.KNOWLEDGE_VERSION,
                0
            ) + 1,

            UPDATED_AT = CURRENT_TIMESTAMP()

    WHEN NOT MATCHED THEN

        INSERT (

            ENTITY_TYPE,

            ENTITY_ID,

            LAST_CONTENT_ID,

            LAST_CONTENT_DATE,

            KNOWLEDGE_VERSION,

            UPDATED_AT

        )

        VALUES (

            S.ENTITY_TYPE,

            S.ENTITY_ID,

            S.LAST_CONTENT_ID,

            S.LAST_CONTENT_DATE,

            1,

            CURRENT_TIMESTAMP()

        )
    """

    query_bq(

        query,

        {

            "entity_type": entity_type,

            "entity_id": entity_id,

            "content_id": content_id,

            "content_date": content_date,

        },

    )
