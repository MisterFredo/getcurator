from datetime import datetime

from .block_service import (
    build_block,
)

from .entity_service import (
    get_entity,
)

from .models import (
    KnowledgeEntityType,
)

from .number_content_service import (
    load_number_batches,
)

from .number_status_repository import (
    get_number_knowledge_cursor,
    update_number_knowledge_cursor,
)

from .repository import (
    exists_general_knowledge,
)


# ============================================================
# BUILD NUMBER KNOWLEDGE
# ============================================================

def build_number_knowledge(
    entity_type: KnowledgeEntityType,
    entity_id: str,
):
    """
    Build the next Knowledge `chiffres` batch
    for one entity.

    Only entities already belonging to the
    general Knowledge perimeter are eligible.

    Numbers use an independent cursor based on:

    - PUBLISHED_AT
    - ID_NUMBER
    """

    # ========================================================
    # VALIDATE ENTITY TYPE
    # ========================================================

    if entity_type not in (
        "company",
        "topic",
        "solution",
    ):

        raise ValueError(
            f"Invalid entity type: {entity_type}"
        )

    # ========================================================
    # CHECK GENERAL KNOWLEDGE SELECTION
    # ========================================================

    if not exists_general_knowledge(
        entity_type=entity_type,
        entity_id=entity_id,
    ):

        raise ValueError(
            "Entity is not selected for "
            "general Knowledge: "
            f"{entity_type}/{entity_id}"
        )

    # ========================================================
    # LOAD ENTITY
    # ========================================================

    entity = get_entity(
        entity_type=entity_type,
        entity_id=entity_id,
    )

    if entity is None:

        raise ValueError(
            "Knowledge entity not found: "
            f"{entity_type}/{entity_id}"
        )

    # ========================================================
    # LOAD NUMBERS CURSOR
    # ========================================================

    (
        last_published_at,
        last_number_id,
    ) = get_number_knowledge_cursor(
        entity_type=entity_type,
        entity_id=entity_id,
    )

    # ========================================================
    # LOAD NEXT NUMBER BATCH
    # ========================================================

    batches = load_number_batches(
        entity_type=entity_type,
        entity_id=entity_id,
        last_published_at=last_published_at,
        last_number_id=last_number_id,
    )

    # ========================================================
    # NOTHING TO PROCESS
    # ========================================================

    if not batches:

        return {
            "status": "no_data",

            "entity_type": entity_type,

            "entity_id": entity_id,

            "entity_name": entity.name,

            "observations_count": 0,

            "batches_count": 0,

            "cursor": {
                "last_published_at": (
                    last_published_at.isoformat()
                    if last_published_at
                    else None
                ),

                "last_number_id": (
                    last_number_id
                ),
            },

            "block": None,
        }

    # ========================================================
    # BUILD KNOWLEDGE BLOCK
    # ========================================================

    block = build_block(
        entity_name=entity.name,
        entity_type=entity_type,
        entity_id=entity_id,
        block_type="chiffres",
        batches=batches,
    )

    # ========================================================
    # RESULT COUNTERS
    # ========================================================

    observations_count = sum(
        len(batch)
        for batch in batches
    )

    last_observation = (
        batches[-1][-1]
    )

    # ========================================================
    # UPDATE NUMBERS CURSOR
    # ========================================================

    update_number_knowledge_cursor(
        entity_type=entity_type,
        entity_id=entity_id,
        last_published_at=(
            last_observation.published_at
        ),
        last_number_id=(
            last_observation.id_number
        ),
        processed_count=(
            observations_count
        ),
    )

    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "status": "built",

        "entity_type": entity_type,

        "entity_id": entity_id,

        "entity_name": entity.name,

        "observations_count": (
            observations_count
        ),

        "batches_count": len(
            batches
        ),

        "last_published_at": (
            last_observation
            .published_at
            .isoformat()
        ),

        "last_number_id": (
            last_observation.id_number
        ),

        "block": {
            "block_type": (
                block.block_type
            ),

            "content": (
                block.content
            ),

            "version": (
                block.version
            ),

            "updated_at": (
                block.updated_at.isoformat()
            ),
        },
    }
