from datetime import (
    datetime,
    timezone,
)

from .builder_service import (
    build_entity,
)

from .repository import (
    get_entity,
    get_block,
    upsert_block,
    get_last_content_date,
    update_last_content,
)

from .models import (
    KnowledgeBlock,
    KnowledgeEntity,
    KnowledgeEntityType,
    KnowledgeBlockType,
)


# ============================================================
# BUILD
# ============================================================

# ============================================================
# BUILD
# ============================================================

def build_knowledge(
    entity_type: KnowledgeEntityType,
    entity_id: str,
):
    """
    Build the next Knowledge batch.
    """

    last_content_date = get_last_content_date(

        entity_type=entity_type,

        entity_id=entity_id,

    )

    last_observation = build_entity(

        entity_type=entity_type,

        entity_id=entity_id,

        last_content_date=last_content_date,

    )

    if last_observation is None:
        return

    update_last_content(

        entity_type=entity_type,

        entity_id=entity_id,

        content_id=last_observation.id,

        content_date=last_observation.published_at,

    )

# ============================================================
# BUILD
# ============================================================

def build_knowledge(
    entity_type: KnowledgeEntityType,
    entity_id: str,
    auto_continue: bool = False,
):
    """
    Build Knowledge.

    By default, processes the next batch only.

    If auto_continue is enabled,
    continues batch by batch until
    no new content remains.
    """

    while True:

        # ====================================================
        # GET CURRENT CURSOR
        # ====================================================

        last_content_date = get_last_content_date(

            entity_type=entity_type,

            entity_id=entity_id,

        )

        # ====================================================
        # BUILD NEXT BATCH
        # ====================================================

        last_observation = build_entity(

            entity_type=entity_type,

            entity_id=entity_id,

            last_content_date=last_content_date,

        )

        # ====================================================
        # NOTHING LEFT
        # ====================================================

        if last_observation is None:
            return

        # ====================================================
        # UPDATE CURSOR
        # ====================================================

        update_last_content(

            entity_type=entity_type,

            entity_id=entity_id,

            content_id=last_observation.id,

            content_date=last_observation.published_at,

        )

        # ====================================================
        # STOP AFTER ONE BATCH
        # ====================================================

        if not auto_continue:
            return


# ============================================================
# GET
# ============================================================

def get_knowledge(
    entity_type: KnowledgeEntityType,
    entity_id: str,
) -> KnowledgeEntity | None:

    return get_entity(

        entity_type=entity_type,

        entity_id=entity_id,

    )


# ============================================================
# UPDATE
# ============================================================

def update_knowledge(
    entity_type: KnowledgeEntityType,
    entity_id: str,
    auto_continue: bool = False,
):
    """
    Update Knowledge with newly
    published contents.
    """

    build_knowledge(

        entity_type=entity_type,

        entity_id=entity_id,

        auto_continue=auto_continue,

    )

# ============================================================
# UPDATE BLOCK
# ============================================================

def update_knowledge_block(
    entity_type: KnowledgeEntityType,
    entity_id: str,
    block_type: KnowledgeBlockType,
    content: str,
) -> KnowledgeBlock:

    block = get_block(

        entity_type=entity_type,

        entity_id=entity_id,

        block_type=block_type,

    )

    if block is None:

        block = KnowledgeBlock(

            block_type=block_type,

            content=content,

            version=1,

            updated_at=datetime.now(
                timezone.utc,
            ),

        )

    else:

        block.content = content

        block.version += 1

        block.updated_at = datetime.now(
            timezone.utc,
        )

    upsert_block(

        entity_type=entity_type,

        entity_id=entity_id,

        block=block,

    )

    return block
