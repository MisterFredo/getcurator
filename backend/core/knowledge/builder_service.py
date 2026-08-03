# backend/core/knowledge/builder_service.py

from .content_service import (
    load_batches,
)

from .block_service import (
    build_block,
)

from .models import (
    KnowledgeEntityType,
)


# ============================================================
# BUILD ENTITY
# ============================================================

def build_entity(
    entity_type: KnowledgeEntityType,
    entity_id: str,
):
    """
    Bootstrap the Knowledge of one entity.

    V1:
    Only the Analytical Signal block
    is generated.
    """

    block_type = "signal_analytique"

    batches = load_batches(

        entity_type=entity_type,

        entity_id=entity_id,

        block_type=block_type,

    )

    if not batches:
        return

    build_block(

        entity_type=entity_type,

        entity_id=entity_id,

        block_type=block_type,

        batches=batches,

    )
