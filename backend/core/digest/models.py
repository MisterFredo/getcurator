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


# ============================================================
# DIGEST DOCUMENT
# ============================================================

class DigestDocument(BaseModel):

    title: str

    subtitle: str = ""

    period: str

    sections: list["DigestSection"]


# ============================================================
# DIGEST SECTION
# ============================================================

class DigestSection(BaseModel):

    title: str

    body: str

    cards: list["DigestCard"] = []


# ============================================================
# DIGEST CARD
# ============================================================

class DigestCard(BaseModel):

    title: str

    excerpt: str

    url: str

    company_logo: str | None = None
