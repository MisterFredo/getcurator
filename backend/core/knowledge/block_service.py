# backend/core/knowledge/block_service.py

from datetime import datetime, timezone
from .models import (
    KnowledgeBlock,
    KnowledgeBlockType,
    KnowledgeContent,
    KnowledgeEntityType,
)

from .repository import (
    get_block,
    upsert_block,
)


# ============================================================
# BUILD BLOCK
# ============================================================

def build_block(
    entity_type: KnowledgeEntityType,
    entity_id: str,
    block_type: KnowledgeBlockType,
    batches: list[list[KnowledgeContent]],
):
    """
    Build one Knowledge Block.

    The consultant starts with an empty notebook.

    Each chronological batch updates
    the notebook until the whole history
    has been processed.
    """

    # --------------------------------------------------------
    # CURRENT BLOCK
    # --------------------------------------------------------

    block = get_block(
        entity_type,
        entity_id,
        block_type,
    )

    if block is None:

        block = KnowledgeBlock(

            block_type=block_type,

            content="",

            version=1,

            updated_at=datetime.now(
                timezone.utc,
            )
        )

    # --------------------------------------------------------
    # PROCESS BATCHES
    # --------------------------------------------------------

    for batch in batches:

        block = _update_block(

            block=block,

            batch=batch,

        )

        upsert_block(

            entity_type=entity_type,

            entity_id=entity_id,

            block=block,

        )

    return block


# ============================================================
# UPDATE BLOCK
# ============================================================

def _update_block(
    block: KnowledgeBlock,
    batch: list[KnowledgeContent],
) -> KnowledgeBlock:
    """
    Update one Knowledge Block from
    one chronological batch.
    """

    raise NotImplementedError
