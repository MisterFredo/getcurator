from core.knowledge.service import (
    get_knowledge,
)

from core.knowledge.entity_service import (
    get_entity as get_entity_metadata,
)

from core.user.user_preferences_service import (
    get_user_preferences_grouped,
)

from .models import (
    ConversationContext,
    ConversationInterlocutorProfile,
    ConversationKnowledgeBlock,
    ConversationKnowledgeEntity,
)

from core.user.user_profile_service import (
    get_user_profile,
)


# ============================================================
# GET INTERLOCUTOR CONTEXT
# ============================================================

def get_interlocutor_context(
    interlocutor_id: str,
) -> ConversationContext:

    # ========================================================
    # PROFILE
    # ========================================================

    raw_profile = get_user_profile(
        interlocutor_id,
    )

    profile = None

    if raw_profile:

        profile = (
            ConversationInterlocutorProfile(
                geography_1=
                    raw_profile.get(
                        "geography_1",
                    ),

                geography_2=
                    raw_profile.get(
                        "geography_2",
                    ),

                geography_3=
                    raw_profile.get(
                        "geography_3",
                    ),

                profile_text=
                    raw_profile.get(
                        "profile_text",
                    ),
            )
        )

    # ========================================================
    # PREFERENCES
    # ========================================================

    preferences = (
        get_user_preferences_grouped(
            interlocutor_id,
        )
        or {}
    )

    # ========================================================
    # COMPANIES
    # ========================================================

    for entity_id in preferences.get(
        "COMPANY",
        [],
    ):

        entity = _build_entity_context(
            entity_type="company",
            entity_id=entity_id,
        )

        if entity:
            entities.append(
                entity,
            )

    # ========================================================
    # TOPICS
    # ========================================================

    for entity_id in preferences.get(
        "TOPIC",
        [],
    ):

        entity = _build_entity_context(
            entity_type="topic",
            entity_id=entity_id,
        )

        if entity:
            entities.append(
                entity,
            )

    # ========================================================
    # SOLUTIONS
    # ========================================================

    for entity_id in preferences.get(
        "SOLUTION",
        [],
    ):

        entity = _build_entity_context(
            entity_type="solution",
            entity_id=entity_id,
        )

        if entity:
            entities.append(
                entity,
            )

    return ConversationContext(
        interlocutor_id=interlocutor_id,
        entities=entities,
    )


# ============================================================
# BUILD ENTITY CONTEXT
# ============================================================

def _build_entity_context(
    entity_type: str,
    entity_id: str,
) -> ConversationKnowledgeEntity | None:
    """
    Build the Conversation representation
    of one Knowledge entity.
    """

    metadata = get_entity_metadata(
        entity_type=entity_type,
        entity_id=entity_id,
    )

    if metadata is None:
        return None

    knowledge = get_knowledge(
        entity_type=entity_type,
        entity_id=entity_id,
    )

    if knowledge is None:
        return None

    blocks: list[
        ConversationKnowledgeBlock
    ] = []

    # ========================================================
    # SIGNAL
    # ========================================================

    if knowledge.signal_analytique.content.strip():

        blocks.append(
            ConversationKnowledgeBlock(
                block_type="signal_analytique",
                content=knowledge.signal_analytique.content,
            )
        )

    # ========================================================
    # MECHANICS
    # ========================================================

    if knowledge.mecanique_expliquee.content.strip():

        blocks.append(
            ConversationKnowledgeBlock(
                block_type="mecanique_expliquee",
                content=knowledge.mecanique_expliquee.content,
            )
        )

    # ========================================================
    # STRATEGIC ISSUE
    # ========================================================

    if knowledge.enjeu_strategique.content.strip():

        blocks.append(
            ConversationKnowledgeBlock(
                block_type="enjeu_strategique",
                content=knowledge.enjeu_strategique.content,
            )
        )

    # ========================================================
    # FRICTION
    # ========================================================

    if knowledge.point_de_friction.content.strip():

        blocks.append(
            ConversationKnowledgeBlock(
                block_type="point_de_friction",
                content=knowledge.point_de_friction.content,
            )
        )

    # ========================================================
    # NUMBERS
    # ========================================================

    if knowledge.chiffres.content.strip():

        blocks.append(
            ConversationKnowledgeBlock(
                block_type="chiffres",
                content=knowledge.chiffres.content,
            )
        )

    if not blocks:
        return None

    return ConversationKnowledgeEntity(
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=metadata.name,
        blocks=blocks,
    )
