from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from core.delivery.models import (
    KnowledgeResult,
)


class DigestRequest(BaseModel):

    user_id: str

    period_start: datetime

    period_end: datetime

    capabilities: list[str]

    limit: int = 20


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


class DigestBatch(BaseModel):

    id: str

    frequency: Literal[
        "weekly",
        "monthly",
    ]

    audience: Literal[
        "user",
        "expert",
    ]

    period_start: datetime

    period_end: datetime

    status: Literal[
        "created",
        "generating",
        "generated",
        "sending",
        "completed",
        "failed",
    ]
    items_count: int = 0
    generated_count: int = 0
    sent_count: int = 0
    failed_count: int = 0
    created_at: datetime

    completed_at: datetime | None = None

class DigestBatchItem(BaseModel):

    id: str

    batch_id: str

    user_id: str

    review_id: str | None = None

    status: Literal[
        "pending",
        "generating",
        "generated",
        "sending",
        "sent",
        "failed",
    ]

    recipients_count: int = 0
    selected_contents: int = 0
    generated_at: datetime | None = None

    sent_at: datetime | None = None

    error: str | None = None

class DigestBatchCreateRequest(BaseModel):

    frequency: Literal[
        "weekly",
        "monthly",
    ]

    audience: Literal[
        "user",
        "expert",
    ]

class DigestProfile(BaseModel):

    user_id: str

    frequency: Literal[
        "weekly",
        "monthly",
    ]

    audience: Literal[
        "user",
        "expert",
    ]

    recipients_count: int
