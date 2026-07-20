# backend/core/delivery/models.py

from typing import Any
from datetime import datetime
from pydantic import BaseModel, Field

from api.expertise.models import (
    Expertise,
)


# ============================================================
# KNOWLEDGE REQUEST
# ============================================================

class KnowledgeRequest(BaseModel):

    user_id: str

    expertise: Expertise | None = None

    content_ids: list[str] = Field(
        default_factory=list,
    )

    number_ids: list[str] = Field(
        default_factory=list,
    )

    capabilities: list[str]


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

# ============================================================
# DELIVERY RESULT
# ============================================================

class DeliveryResult(BaseModel):

    success: bool

    recipient: str

    provider: str

    message_id: str | None = None

    sent_at: datetime | None = None

    error: str | None = None
