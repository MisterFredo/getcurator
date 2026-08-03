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

def build_knowledge(
    entity_type: KnowledgeEntityType,
    entity_id: str,
):

    build_entity(
        entity_type=entity_type,
        entity_id=entity_id,
    )


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
):

    raise NotImplementedError


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
