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

    block_type: KnowledgeBlockType

    content: str

    version: int

    updated_at: datetime


# ============================================================
# KNOWLEDGE ENTITY
# ============================================================

class KnowledgeEntity(BaseModel):

    entity_type: KnowledgeEntityType

    entity_id: str

    signal_analytique: KnowledgeBlock

    mecanique_expliquee: KnowledgeBlock

    enjeu_strategique: KnowledgeBlock

    point_de_friction: KnowledgeBlock

    chiffres: KnowledgeBlock

    updated_at: datetime

# ============================================================
# KNOWLEDGE REQUEST
# ============================================================

class KnowledgeRequest(BaseModel):

    entity_type: KnowledgeEntityType

    entity_id: str

# ============================================================
# KNOWLEDGE CONTENT
# ============================================================

class KnowledgeContent(BaseModel):
    """
    One enriched content used by
    the Knowledge Builder.
    """

    id: str

    title: str

    excerpt: str

    signal_analytique: str

    mecanique_expliquee: str

    enjeu_strategique: str

    point_de_friction: str

    chiffres: str

    published_at: datetime

class KnowledgeBlockUpdateRequest(BaseModel):

    entity_type: KnowledgeEntityType

    entity_id: str

    block_type: KnowledgeBlockType

    content: str
