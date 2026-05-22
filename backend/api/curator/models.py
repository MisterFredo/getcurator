from pydantic import (
    BaseModel,
    Field,
)

from typing import (
    List,
    Optional,
    Literal,
)

from datetime import datetime


# ============================================================
# CORE ENTITIES
# ============================================================

class Topic(BaseModel):

    id_topic: str

    label: str

    axis: Optional[str] = None


class Company(BaseModel):

    id_company: str

    name: str


class Solution(BaseModel):

    id_solution: str

    name: str


class Concept(BaseModel):

    id_concept: str

    label: str


# ============================================================
# FEED
# ============================================================

class FeedItem(BaseModel):

    id: str

    type: Literal[
        "news",
        "analysis",
    ]

    title: str

    excerpt: Optional[str] = None

    content_body: Optional[str] = None

    published_at: Optional[datetime] = None

    source_url: Optional[str] = None

    source_title: Optional[str] = None

    # --------------------------------------------------------
    # PRIMARY COMPANY
    # --------------------------------------------------------

    id_primary_company: Optional[str] = None

    # --------------------------------------------------------
    # ENTITIES
    # --------------------------------------------------------

    topics: List[Topic] = Field(
        default_factory=list
    )

    companies: List[Company] = Field(
        default_factory=list
    )

    solutions: List[Solution] = Field(
        default_factory=list
    )

    concepts: List[Concept] = Field(
        default_factory=list
    )

    # --------------------------------------------------------
    # BADGES / UNIVERS
    # --------------------------------------------------------

    badges: List[dict] = Field(
        default_factory=list
    )

    universes: List[dict] = Field(
        default_factory=list
    )


class FeedResponse(BaseModel):

    items: List[FeedItem]

    count: int


# ============================================================
# 🔥 NUMBERS (V1 — BACKLOG)
# ============================================================

class CuratorNumberItem(BaseModel):

    id: str

    type: Literal["number_backlog"]

    label: Optional[str] = None

    value: Optional[float] = None

    unit: Optional[str] = None

    zone: Optional[str] = None

    period: Optional[str] = None

    actor: Optional[str] = None

    context_title: Optional[str] = None

    published_at: Optional[datetime] = None


class CuratorNumbersResponse(BaseModel):

    items: List[CuratorNumberItem]

    count: int


# ============================================================
# STATS
# ============================================================

class StatsItem(BaseModel):

    total_count: int

    last_7_days: int

    last_30_days: int


class TopicStats(StatsItem):

    id_topic: str

    label: str


class CompanyStats(StatsItem):

    id_company: str

    name: str


class SolutionStats(StatsItem):

    id_solution: str

    name: str


class ContentStatsResponse(BaseModel):

    total_count: int

    last_7_days: int

    last_30_days: int

    topics_stats: List[TopicStats]

    top_companies: List[CompanyStats]

    top_solutions: List[SolutionStats]
