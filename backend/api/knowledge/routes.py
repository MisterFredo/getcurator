# backend/api/knowledge/routes.py

from fastapi import (
    APIRouter,
)

from core.knowledge.models import (
    KnowledgeRequest,
    KnowledgeBlockUpdateRequest,
)

from core.knowledge.service import (
    build_knowledge,
    get_knowledge,
    update_knowledge,
    update_knowledge_block,
)

from core.knowledge.cockpit_service import (
    get_dashboard,
    list_entities,
)


router = APIRouter()


# ============================================================
# DASHBOARD
# ============================================================

@router.get(
    "/dashboard",
)
def get_dashboard_route():
    """
    Return global Knowledge statistics.
    """

    return {

        "status": "ok",

        "dashboard": get_dashboard(),

    }


# ============================================================
# EXPLORER
# ============================================================

@router.get(
    "/explorer",
)
def list_entities_route():
    """
    Return every entity displayed in the
    Knowledge Explorer.
    """

    return {

        "status": "ok",

        "explorer": list_entities(),

    }


# ============================================================
# BUILD
# ============================================================

@router.post(
    "/build",
)
def build_knowledge_route(
    request: KnowledgeRequest,
):
    """
    Bootstrap the complete Knowledge
    of one entity.
    """

    build_knowledge(

        entity_type=request.entity_type,

        entity_id=request.entity_id,

    )

    return {

        "status": "ok",

    }


# ============================================================
# UPDATE
# ============================================================

@router.post(
    "/update",
)
def update_knowledge_route(
    request: KnowledgeRequest,
):
    """
    Update the Knowledge of one entity
    using newly available contents.
    """

    update_knowledge(

        entity_type=request.entity_type,

        entity_id=request.entity_id,

    )

    return {

        "status": "ok",

    }


# ============================================================
# GET ENTITY
# ============================================================

@router.get(
    "/{entity_type}/{entity_id}",
)
def get_knowledge_route(
    entity_type: str,
    entity_id: str,
):
    """
    Return the complete Knowledge
    of one entity.
    """

    return {

        "status": "ok",

        "knowledge": get_knowledge(

            entity_type=entity_type,

            entity_id=entity_id,

        ),

    }


# ============================================================
# UPDATE BLOCK
# ============================================================

@router.put(
    "/block",
)
def update_knowledge_block_route(
    request: KnowledgeBlockUpdateRequest,
):
    """
    Manually edit one Knowledge Block.
    """

    block = update_knowledge_block(

        entity_type=request.entity_type,

        entity_id=request.entity_id,

        block_type=request.block_type,

        content=request.content,

    )

    return {

        "status": "ok",

        "block": block,

    }
