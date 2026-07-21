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
# DIGEST
# ============================================================

class Digest(BaseModel):

    id: str = Field(
        default_factory=lambda: str(uuid4())
    )

    campaign_id: str

    request: DigestRequest

    status: Literal[
        "pending",
        "generating",
        "generated",
        "sending",
        "sent",
        "failed",
    ] = "pending"

    total_contents: int = 0

    analyzed_contents: int = 0

    knowledge: KnowledgeResult | None = None

    document: DigestDocument | None = None

    generated_at: datetime | None = None

    sent_at: datetime | None = None

    error: str | None = None


# ============================================================
# CAMPAIGN
# ============================================================

class Campaign(BaseModel):

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

    digests_count: int = 0

    generated_count: int = 0

    sent_count: int = 0

    failed_count: int = 0

    created_at: datetime

    completed_at: datetime | None = None


# ============================================================
# CAMPAIGN CREATE REQUEST
# ============================================================

class CampaignCreateRequest(BaseModel):

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
# CAMPAIGN DETAIL
# ============================================================

class CampaignDetail(BaseModel):

    campaign: Campaign

    digests: list[Digest]
