from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    Field,
)


# ============================================================
# TYPES
# ============================================================

DigestCandidateSource = Literal[
    "FAVORITE_COMPANY",
    "FAVORITE_SOLUTION",
    "FAVORITE_TOPIC",
    "PROFILE_ENTITY",
    "PROFILE_TERM",
]

DigestCandidatePriority = Literal[
    "SELECT",
    "IGNORE",
]


# ============================================================
# STRICT MODEL
# ============================================================

class StrictDigestSelectionModel(
    BaseModel,
):

    class Config:

        extra = "forbid"


# ============================================================
# LIGHT CONTENT CANDIDATE
# ============================================================

class DigestContentCandidate(
    StrictDigestSelectionModel,
):

    content_id: str

    title: str

    excerpt: str = ""

    source_title: str = ""

    published_at: datetime | None = None

    selection_sources: list[
        DigestCandidateSource
    ] = Field(
        default_factory=list,
    )

    matched_favorites: list[str] = Field(
        default_factory=list,
    )

    matched_watch_instructions: list[str] = Field(
        default_factory=list,
    )

    matched_profile_terms: list[str] = Field(
        default_factory=list,
    )


# ============================================================
# LLM CONTENT DECISION
# ============================================================

class DigestContentDecision(
    StrictDigestSelectionModel,
):

    content_id: str

    priority: DigestCandidatePriority

    relevance_score: int = Field(
        ...,
        ge=0,
        le=100,
    )

    reason: str

    matched_priorities: list[str] = Field(
        default_factory=list,
    )


# ============================================================
# LLM SELECTION RESULT
# ============================================================

class DigestCandidateSelectionResult(
    StrictDigestSelectionModel,
):

    decisions: list[
        DigestContentDecision
    ] = Field(
        default_factory=list,
    )

# ============================================================
# SELECTION OUTCOME
# ============================================================

class DigestSelectionOutcome(
    StrictDigestSelectionModel,
):

    selection: DigestCandidateSelectionResult

    selected_content_ids: list[str] = Field(
        default_factory=list,
    )

    used_fallback: bool = False

    error: str | None = None
