# backend/core/knowledge/builder_service.py

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

    Process:
        1. Load every related content.
        2. Sort chronologically.
        3. Split into batches.
        4. Build each Knowledge Block.
        5. Save every block.
    """

    # --------------------------------------------------------
    # LOAD CONTENTS
    # --------------------------------------------------------

    contents = _load_contents(
        entity_type,
        entity_id,
    )

    if not contents:
        return

    # --------------------------------------------------------
    # SPLIT BATCHES
    # --------------------------------------------------------

    batches = _split_batches(
        contents,
    )

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
# LOAD CONTENTS
# ============================================================

def _load_contents(
    entity_type: KnowledgeEntityType,
    entity_id: str,
):
    """
    Load every content associated
    with the entity.

    Ordered from oldest to newest.
    """

    raise NotImplementedError


# ============================================================
# SPLIT BATCHES
# ============================================================

def _split_batches(
    contents,
    batch_size: int = 50,
):
    """
    Split chronological contents
    into batches.
    """

    raise NotImplementedError


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

    Each batch updates the notes
    produced by the previous batch.
    """

    raise NotImplementedError
