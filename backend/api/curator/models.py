from pydantic import BaseModel, Field
from typing import List, Optional, Literal
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
    title: str


# ============================================================
# FEED (CONTENT)
# ============================================================

class FeedItem(BaseModel):
    id: str

    # 🔥 NEW
    type: Literal["NEWS", "ANALYSIS"]

    title: str
    excerpt: Optional[str] = None
    published_at: Optional[datetime] = None

    # 🔥 NEW
    primary_company: Optional[Company] = None

    topics: List[Topic] = Field(default_factory=list)
    companies: List[Company] = Field(default_factory=list)
    solutions: List[Solution] = Field(default_factory=list)

    concepts: List[Concept] = Field(default_factory=list)


class FeedResponse(BaseModel):
    items: List[FeedItem]
    count: int


# ============================================================
# 🔥 NUMBERS (V1 — BACKLOG)
# ============================================================

class CuratorNumberItem(BaseModel):

    id: str
    type: Literal["number_backlog"]

    # 🔢 NUMBER
    label: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None

    zone: Optional[str] = None
    period: Optional[str] = None
    actor: Optional[str] = None

    # 🧠 CONTEXT
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
