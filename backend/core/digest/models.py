from datetime import (
    datetime,
    timezone,
)
from typing import Literal
from uuid import uuid4

from pydantic import (
    BaseModel,
    Field,
)

from core.delivery.models import (
    KnowledgeResult,
)


# ============================================================
# DIGEST REQUEST
# ============================================================

class DigestRequest(BaseModel):

    user_id: str

    period_start: datetime

    period_end: datetime

    capabilities: list[str]

    limit: int = 20


# ============================================================
# DIGEST CARD
# ============================================================

class DigestCard(BaseModel):

    id: str

    title: str

    excerpt: str

    url: str

    source_title: str | None = None

    published_at: datetime | None = None

    company_logo: str | None = None


# ============================================================
# DIGEST SECTION
# ============================================================

class DigestSection(BaseModel):

    id: str

    title: str

    body: str

    cards: list[DigestCard] = Field(
        default_factory=list,
    )


# ============================================================
# DIGEST DOCUMENT
# ============================================================

class DigestDocument(BaseModel):

    title: str

    subtitle: str = ""

    period: str

    sections: list[DigestSection]


# ============================================================
# DIGEST REVIEW
# ============================================================

class DigestReview(BaseModel):

    id: str = Field(
        default_factory=lambda: str(uuid4())
    )

    request: DigestRequest

    total_contents: int

    analyzed_contents: int

    knowledge: KnowledgeResult

    document: DigestDocument | None = None

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        )
    )


# ============================================================
# DIGEST BATCH
# ============================================================

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
        "prepared",
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


# ============================================================
# DIGEST BATCH ITEM
# ============================================================

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

    selected_contents: int = 0

    generated_at: datetime | None = None

    sent_at: datetime | None = None

    error: str | None = None


# ============================================================
# DIGEST BATCH CREATE REQUEST
# ============================================================

class DigestBatchCreateRequest(BaseModel):

    frequency: Literal[
        "weekly",
        "monthly",
    ]

    audience: Literal[
        "user",
        "expert",
    ]


# ============================================================
# DIGEST PROFILE
# ============================================================

class DigestProfile(BaseModel):

    user_id: str

    language: str = "en"

    frequency: Literal[
        "weekly",
        "monthly",
    ]

    audience: Literal[
        "user",
        "expert",
    ]


# ============================================================
# DIGEST BATCH DETAIL
# ============================================================

class DigestBatchDetail(BaseModel):

    batch: DigestBatch

    items: list[DigestBatchItem]
