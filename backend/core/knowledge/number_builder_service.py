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


# ============================================================
# BUILD NUMBER KNOWLEDGE
# ============================================================

def build_number_knowledge(
    entity_type: KnowledgeEntityType,
    entity_id: str,
    last_published_at: datetime | None = None,
):
    """
    Build only the Knowledge `chiffres` block
    for one entity.

    This service is intentionally independent
    from the general Knowledge builder.
    """

    if entity_type not in (
        "company",
        "topic",
        "solution",
    ):

        raise ValueError(
            f"Invalid entity type: {entity_type}"
        )

    entity = get_entity(

        entity_type=entity_type,

        entity_id=entity_id,

    )

    if entity is None:

        raise ValueError(
            "Knowledge entity not found: "
            f"{entity_type}/{entity_id}"
        )

    batches = load_number_batches(

        entity_type=entity_type,

        entity_id=entity_id,

        last_published_at=last_published_at,

    )

    if not batches:

        return {
            "status": "no_data",
            "entity_type": entity_type,
            "entity_id": entity_id,
            "entity_name": entity.name,
            "observations_count": 0,
            "batches_count": 0,
            "block": None,
        }

    block = build_block(

        entity_name=entity.name,

        entity_type=entity_type,

        entity_id=entity_id,

        block_type="chiffres",

        batches=batches,

    )

    observations_count = sum(
        len(batch)
        for batch in batches
    )

    last_observation = (
        batches[-1][-1]
    )

    return {
        "status": "built",
        "entity_type": entity_type,
        "entity_id": entity_id,
        "entity_name": entity.name,
        "observations_count": (
            observations_count
        ),
        "batches_count": len(batches),
        "last_published_at": (
            last_observation
            .published_at
            .isoformat()
        ),
        "block": {
            "block_type": block.block_type,
            "content": block.content,
            "version": block.version,
            "updated_at": (
                block.updated_at.isoformat()
            ),
        },
    }
