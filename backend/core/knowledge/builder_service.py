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
    """

    batches = load_batches(
        entity_type,
        entity_id,
    )

    if not batches:
        return

    for block_type in [

        "signal_analytique",

        "mecanique_expliquee",

        "enjeu_strategique",

        "point_de_friction",

        "chiffres",

    ]:

        build_block(

            entity_type=entity_type,

            entity_id=entity_id,

            block_type=block_type,

            batches=batches,

        )
