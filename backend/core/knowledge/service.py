# backend/core/knowledge/service.py

from .builder_service import (
    build_entity,
)

from .repository import (
    get_entity,
)

from .models import (
    KnowledgeEntity,
    KnowledgeEntityType,
)


# ============================================================
# BUILD
# ============================================================

def build_knowledge(
    entity_type: KnowledgeEntityType,
    entity_id: str,
):
    """
    Bootstrap the Knowledge of one entity.
    """

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
    """
    Return the Knowledge of one entity.
    """

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
    """
    Update the Knowledge of one entity.

    Placeholder for incremental updates.
    """

    raise NotImplementedError
