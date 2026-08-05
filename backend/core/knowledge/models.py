# backend/core/knowledge/models.py

from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
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
# KNOWLEDGE ENTITY SUMMARY
# ============================================================

class KnowledgeEntitySummary(BaseModel):

    entity_type: KnowledgeEntityType

    entity_id: str

    name: str

    contents_count: int

    processed_contents: int

    users_count: int

    experts_count: int

    last_content_date: datetime | None

    updated_at: datetime | None
# ============================================================
# KNOWLEDGE EXPLORER
# ============================================================

class KnowledgeExplorer(BaseModel):

    entities: list[KnowledgeEntitySummary]


# ============================================================
# KNOWLEDGE DASHBOARD
# ============================================================

class KnowledgeDashboard(BaseModel):

    companies: int

    topics: int

    solutions: int

    entities: int

    knowledge_built: int

    users: int

    experts: int

# ============================================================
# KNOWLEDGE REQUEST
# ============================================================

class KnowledgeRequest(BaseModel):

    entity_type: KnowledgeEntityType

    entity_id: str

    limit: int | None = None


# ============================================================
# KNOWLEDGE OBSERVATION
# ============================================================

class KnowledgeObservation(BaseModel):
    """
    One observation sent to one Knowledge Agent.

    The meaning of `content` depends on the Agent:

    - Signal Agent              -> signal_analytique
    - Mechanics Agent           -> mecanique_expliquee
    - Strategic Agent           -> enjeu_strategique
    - Friction Agent            -> point_de_friction
    - Numbers Agent             -> chiffres
    """

    id: str

    title: str

    excerpt: str

    content: str

    published_at: datetime


# ============================================================
# KNOWLEDGE BLOCK UPDATE
# ============================================================

class KnowledgeBlockUpdateRequest(BaseModel):

    entity_type: KnowledgeEntityType

    entity_id: str

    block_type: KnowledgeBlockType

    content: str
