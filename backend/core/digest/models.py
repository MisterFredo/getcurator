from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from core.delivery.models import (
    KnowledgeResult,
)


# ============================================================
# DIGEST REQUEST
# ============================================================

class DigestRequest(BaseModel):

    user_id: str

    target_type: Literal[
        "user",
        "expert",
    ]

    expert_id: str | None = None

    period_start: datetime

    period_end: datetime

    capabilities: list[str]


# ============================================================
# DIGEST REVIEW
# ============================================================

class DigestReview(BaseModel):

    request: DigestRequest

    total_contents: int

    analyzed_contents: int

    knowledge: KnowledgeResult
