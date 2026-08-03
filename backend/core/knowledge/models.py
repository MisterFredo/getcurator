# backend/core/knowledge/models.py

from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    Field,
)


# ============================================================
# TYPES
# ============================================================

KnowledgeEntityType = Literal[
    "company",
    "topic",
    "solution",
]

KnowledgeBlockType = Literal[
    "signal_analytique",
    "mecanique_expliquee",
    "enjeu_strategique",
    "point_de_friction",
    "chiffres",
]


# ============================================================
# KNOWLEDGE BLOCK
# ============================================================

class KnowledgeBlock(BaseModel):
    """
    Consultant notes for one knowledge block.
    """

    block_type: KnowledgeBlockType

    notes: list[str] = Field(
        default_factory=list,
    )

    version: int = 1

    updated_at: datetime


# ============================================================
# KNOWLEDGE ENTITY
# ============================================================

class KnowledgeEntity(BaseModel):

    entity_type: ...

    entity_id: ...

    signal_analytique: KnowledgeBlock

    mecanique_expliquee: KnowledgeBlock

    enjeu_strategique: KnowledgeBlock

    point_de_friction: KnowledgeBlock

    chiffres: KnowledgeBlock

    updated_at: datetime

# ============================================================
# KNOWLEDGE UPDATE
# ============================================================

class KnowledgeUpdate(BaseModel):
    """
    One new observation used to update
    one Knowledge Block.
    """

    title: str

    excerpt: str

    content: str


# ============================================================
# KNOWLEDGE REQUEST
# ============================================================

class KnowledgeRequest(BaseModel):

    entity_type: KnowledgeEntityType

    entity_id: str
