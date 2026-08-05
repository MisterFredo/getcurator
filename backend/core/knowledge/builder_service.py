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
    KnowledgeObservation,
)


# ============================================================
# BUILD ENTITY
# ============================================================

def build_entity(
    entity_type: KnowledgeEntityType,
    entity_id: str,
    last_content_date=None,
):
    """
    Build the next Knowledge batch
    for one entity.

    Returns
    -------
    The last processed observation,
    or None if no new content exists.
    """

    # ========================================================
    # LOAD ENTITY
    # ========================================================

    entity = get_entity(

        entity_type=entity_type,

        entity_id=entity_id,

    )

    if entity is None:
        return None

    last_observation: KnowledgeObservation | None = None

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

            last_content_date=last_content_date,

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

        # ====================================================
        # KEEP LAST OBSERVATION
        # ====================================================

        last_batch = batches[-1]

        if last_batch:

            last_observation = last_batch[-1]

    return last_observation
