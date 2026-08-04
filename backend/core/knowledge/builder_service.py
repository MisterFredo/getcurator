# backend/core/knowledge/builder_service.py

from .content_service import (
    load_batches,
)

from .block_service import (
    build_block,
)

from .entity_service import (
    get_entity,
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

    Each Knowledge Block is built
    independently from its own
    observations.
    """

    # ========================================================
    # LOAD ENTITY
    # ========================================================

    entity = get_entity(

        entity_type=entity_type,

        entity_id=entity_id,

    )

    if entity is None:
        return

    # ========================================================
    # BUILD BLOCKS
    # ========================================================

    for block_type in [

        "signal_analytique",

        "mecanique_expliquee",

        "enjeu_strategique",

        "point_de_friction",

    ]:

        batches = load_batches(

            entity_type=entity_type,

            entity_id=entity_id,

            block_type=block_type,

        )

        if not batches:
            continue

        build_block(

            entity_name=entity.name,

            entity_type=entity_type,

            entity_id=entity_id,

            block_type=block_type,

            batches=batches,

        )
