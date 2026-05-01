from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


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


# 🔥 NEW
class Concept(BaseModel):
    id_concept: str
    title: str


class FeedItem(BaseModel):
    id: str
    type: Literal["news", "analysis"]

    title: str
    excerpt: Optional[str] = None
    published_at: Optional[datetime] = None

    topics: List[Topic] = Field(default_factory=list)
    companies: List[Company] = Field(default_factory=list)
    solutions: List[Solution] = Field(default_factory=list)

    # 🔥 NEW
    concepts: List[Concept] = Field(default_factory=list)

    news_type: Optional[str] = None


class FeedResponse(BaseModel):
    items: List[FeedItem]
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
