from typing import (
    Literal,
)

from pydantic import (
    BaseModel,
    Field,
)

from core.knowledge.models import (
    KnowledgeBlockType,
    KnowledgeEntityType,
)


# ============================================================
# TYPES
# ============================================================

ConversationRole = Literal[
    "user",
    "assistant",
]


# ============================================================
# MESSAGE
# ============================================================

class ConversationMessage(BaseModel):
    """
    One previous message in the conversation.
    """

    role: ConversationRole

    content: str


# ============================================================
# REQUEST
# ============================================================

class ConversationRequest(BaseModel):
    """
    One question asked to one interlocutor.

    An interlocutor is technically a user:
    - the current user ("Moi augmenté")
    - or an Expert
    """

    interlocutor_id: str

    question: str

    history: list[ConversationMessage] = Field(
        default_factory=list,
    )


# ============================================================
# KNOWLEDGE BLOCK CONTEXT
# ============================================================

class ConversationKnowledgeBlock(BaseModel):
    """
    One Knowledge Block exposed to Conversation.
    """

    block_type: KnowledgeBlockType

    content: str


# ============================================================
# KNOWLEDGE ENTITY CONTEXT
# ============================================================

class ConversationKnowledgeEntity(BaseModel):
    """
    Knowledge available for one entity
    followed by the interlocutor.
    """

    entity_type: KnowledgeEntityType

    entity_id: str

    entity_name: str

    blocks: list[
        ConversationKnowledgeBlock
    ] = Field(
        default_factory=list,
    )


# ============================================================
# CONTEXT
# ============================================================

class ConversationContext(BaseModel):
    """
    Complete Knowledge context available
    for one interlocutor.
    """

    interlocutor_id: str

    entities: list[
        ConversationKnowledgeEntity
    ] = Field(
        default_factory=list,
    )


# ============================================================
# RESPONSE
# ============================================================

class ConversationResponse(BaseModel):
    """
    Final answer returned by the
    Conversation Engine.
    """

    interlocutor_id: str

    answer: str
