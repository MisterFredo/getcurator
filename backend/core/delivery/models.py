# backend/core/delivery/models.py

from typing import Any

from pydantic import BaseModel, Field

from api.expertise.models import (
    Expertise,
)


# ============================================================
# KNOWLEDGE REQUEST
# ============================================================

class KnowledgeRequest(BaseModel):

    # ========================================================
    # CONTEXT
    # ========================================================

    user_id: str

    # ========================================================
    # REQUEST
    # ========================================================

    capabilities: list[str]

    content_ids: list[str] = Field(
        default_factory=list,
    )

    number_ids: list[str] = Field(
        default_factory=list,
    )

    expert_id: str | None = None

    period: str | None = None

    # ========================================================
    # EXTENSIONS
    # ========================================================

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# KNOWLEDGE RESULT
# ============================================================

class KnowledgeResult(BaseModel):

    # ========================================================
    # EXPERTISE
    # ========================================================

    expertise: Expertise

    # ========================================================
    # CAPABILITIES
    # ========================================================

    capability_results: dict[str, str] = Field(
        default_factory=dict,
    )

    # ========================================================
    # EXTENSIONS
    # ========================================================

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )
