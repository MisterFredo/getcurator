# backend/core/knowledge/block_service.py

from datetime import (
    datetime,
    timezone,
)

from utils.llm import (
    run_llm,
)

from .models import (
    KnowledgeBlock,
    KnowledgeBlockType,
    KnowledgeObservation,
    KnowledgeEntityType,
)

from .repository import (
    get_block,
    upsert_block,
)

from .prompts.signal import (
    build_signal_prompt,
)

from .prompts.mecanique import (
    build_mecanique_prompt,
)

from .prompts.enjeu import (
    build_enjeu_prompt,
)

from .prompts.friction import (
    build_friction_prompt,
)


# ============================================================
# BUILD BLOCK
# ============================================================

def build_block(
    entity_name: str,
    entity_type: KnowledgeEntityType,
    entity_id: str,
    block_type: KnowledgeBlockType,
    batches: list[list[KnowledgeObservation]],
):
    """
    Build one Knowledge Block.

    The consultant starts with an empty notebook.

    Each chronological batch updates
    the notebook until the whole history
    has been processed.
    """

    # ========================================================
    # LOAD CURRENT BLOCK
    # ========================================================

    block = get_block(
        entity_type,
        entity_id,
        block_type,
    )

    if block is None:

        block = KnowledgeBlock(

            block_type=block_type,

            content="",

            version=1,

            updated_at=datetime.now(
                timezone.utc,
            ),

        )

    # ========================================================
    # PROCESS CHRONOLOGICAL BATCHES
    # ========================================================

    for batch in batches:

        block = _update_block(

            entity_name=entity_name,

            entity_type=entity_type,

            block=block,

            batch=batch,

        )

        upsert_block(

            entity_type=entity_type,

            entity_id=entity_id,

            block=block,

        )

    return block


# ============================================================
# UPDATE BLOCK
# ============================================================

def _update_block(
    entity_name: str,
    entity_type: KnowledgeEntityType,
    block: KnowledgeBlock,
    batch: list[KnowledgeObservation],
) -> KnowledgeBlock:
    """
    Update one Knowledge Block from
    one chronological batch.
    """

    prompt = _build_prompt(

        entity_name=entity_name,

        entity_type=entity_type,

        block_type=block.block_type,

        block=block,

        batch=batch,

    )

    content = run_llm(

        prompt=prompt,

        temperature=0.2,

    ) or block.content

    return KnowledgeBlock(

        block_type=block.block_type,

        content=content.strip(),

        version=block.version + 1,

        updated_at=datetime.now(
            timezone.utc,
        ),

    )


# ============================================================
# BUILD PROMPT
# ============================================================

def _build_prompt(
    entity_name: str,
    entity_type: KnowledgeEntityType,
    block_type: KnowledgeBlockType,
    block: KnowledgeBlock,
    batch: list[KnowledgeObservation],
) -> str:
    """
    Dispatch to the appropriate
    prompt builder.
    """

    match block_type:

        case "signal_analytique":
    
            return build_signal_prompt(
    
                entity_name=entity_name,
    
                entity_type=entity_type,
    
                block=block,
    
                contents=batch,
    
            )
    
        case "mecanique_expliquee":
    
            return build_mecanique_prompt(
    
                entity_name=entity_name,
    
                entity_type=entity_type,
    
                block=block,
    
                contents=batch,
    
            )
    
        case "enjeu_strategique":
    
            return build_enjeu_prompt(
    
                entity_name=entity_name,
    
                entity_type=entity_type,
    
                block=block,
    
                contents=batch,
    
            )
    
        case "point_de_friction":
    
            return build_friction_prompt(
    
                entity_name=entity_name,
    
                entity_type=entity_type,
    
                block=block,
    
                contents=batch,
    
            )
    
        case "chiffres":

            # Handled by a dedicated Knowledge Agent

            raise NotImplementedError

    raise ValueError(
        f"Unknown block type: {block_type}"
    )
