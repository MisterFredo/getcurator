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
# TYPES
# ============================================================

DigestFrequency = Literal[
    "weekly",
]

DigestAudience = Literal[
    "user",
    "expert",
]


# ============================================================
# DIGEST BADGE
# ============================================================

class DigestBadge(
    BaseModel,
):

    label: str

    type: Literal[
        "company",
        "topic",
        "solution",
        "keyword",
    ]


# ============================================================
# DIGEST PROFILE
# ============================================================

class DigestProfile(
    BaseModel,
):

    name: str

    company: str | None = None

    role: str | None = None

    description: str | None = None

    geography_1: str | None = None

    geography_2: str | None = None

    geography_3: str | None = None

    companies: list[DigestBadge] = Field(
        default_factory=list,
    )

    topics: list[DigestBadge] = Field(
        default_factory=list,
    )

    solutions: list[DigestBadge] = Field(
        default_factory=list,
    )

    keywords: list[str] = Field(
        default_factory=list,
    )


# ============================================================
# DIGEST CARD
# ============================================================

class DigestCard(
    BaseModel,
):

    id: str

    title: str

    excerpt: str

    url: str

    source_title: str | None = None

    published_at: datetime | None = None

    badges: list[DigestBadge] = Field(
        default_factory=list,
    )

    matching_badges: list[DigestBadge] = Field(
        default_factory=list,
    )


# ============================================================
# DIGEST SECTION
# ============================================================

class DigestSection(
    BaseModel,
):

    title: str

    content: str

    cards: list[DigestCard] = Field(
        default_factory=list,
    )


# ============================================================
# DIGEST DOCUMENT
# ============================================================

class DigestDocument(
    BaseModel,
):

    title: str

    subtitle: str = ""

    period: str

    created_at: datetime

    profile: DigestProfile

    sections: list[DigestSection] = Field(
        default_factory=list,
    )

    frequency: DigestFrequency

    audience: DigestAudience


# ============================================================
# DIGEST
# ============================================================

class Digest(
    BaseModel,
):

    id: str = Field(
        default_factory=lambda: str(
            uuid4()
        ),
    )

    campaign_id: str

    user_id: str

    status: Literal[
        "created",
        "generating",
        "generated",
        "sending",
        "sent",
        "failed",
    ]

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

class Campaign(
    BaseModel,
):

    id: str = Field(
        default_factory=lambda: str(
            uuid4()
        ),
    )

    frequency: DigestFrequency

    audience: DigestAudience

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

    created_at: datetime = Field(

        default_factory=lambda: datetime.now(
            timezone.utc,
        )

    )

    completed_at: datetime | None = None


# ============================================================
# CAMPAIGN CREATE REQUEST
# ============================================================

class CampaignCreateRequest(
    BaseModel,
):

    # Retained in the API payload for compatibility,
    # but only weekly is accepted.

    frequency: DigestFrequency = "weekly"

    audience: DigestAudience


# ============================================================
# CAMPAIGN DIGEST
# ============================================================

class CampaignDigest(
    Digest,
):

    user_name: str | None = None

    user_email: str | None = None


# ============================================================
# CAMPAIGN DETAIL
# ============================================================

class CampaignDetail(
    BaseModel,
):

    campaign: Campaign

    digests: list[CampaignDigest] = Field(
        default_factory=list,
    )


# ============================================================
# DIGEST RECIPIENT
# ============================================================

class DigestRecipient(
    BaseModel,
):

    user_id: str

    language: str
