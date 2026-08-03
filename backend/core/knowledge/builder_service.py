# backend/core/knowledge/builder_service.py

from .content_service import (
    load_batches,
)

from .models import (
    KnowledgeBlockType,
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
    """

    # --------------------------------------------------------
    # LOAD BATCHES
    # --------------------------------------------------------

    batches = load_batches(
        entity_type,
        entity_id,
    )

    if not batches:
        return

    # --------------------------------------------------------
    # BUILD EVERY BLOCK
    # --------------------------------------------------------

    for block_type in [

        "signal_analytique",

        "mecanique_expliquee",

        "enjeu_strategique",

        "point_de_friction",

        "chiffres",

    ]:

        _build_block(

            entity_type=entity_type,

            entity_id=entity_id,

            block_type=block_type,

            batches=batches,

        )


# ============================================================
# BUILD BLOCK
# ============================================================

def _build_block(
    entity_type: KnowledgeEntityType,
    entity_id: str,
    block_type: KnowledgeBlockType,
    batches,
):
    """
    Build one Knowledge Block.

    Each chronological batch updates
    the consultant notes produced by
    the previous batch.
    """

    raise NotImplementedError
