from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

# =======================================================
# ANALYSIS — FEED
# =======================================================

class AnalysisItem(BaseModel):
    id: str
    title: str
    excerpt: Optional[str]
    published_at: datetime


class AnalysisListResponse(BaseModel):
    items: List[AnalysisItem]


# =======================================================
# ANALYSIS — DETAIL
# =======================================================

class ContentDetailResponse(BaseModel):
    id_content: str
    title: str
    excerpt: Optional[str]
    content_body: Optional[str]

    chiffres: List[str]
    acteurs_cites: List[str]

    # LLM
    concepts_llm: List[str]
    solutions_llm: List[str]
    topics_llm: List[str]

    # STRUCTURÉ
    concepts: Optional[List[dict]] = None
    solutions: Optional[List[dict]] = None

    published_at: Optional[datetime]

    topics: Optional[List[dict]] = None
    companies: Optional[List[dict]] = None


# =======================================================
# DRAWER — NEWS
# =======================================================

class DrawerNewsResponse(BaseModel):
    id_news: str
    title: str
    excerpt: Optional[str]
    body: Optional[str]
    published_at: datetime
    visual_rect_id: Optional[str] = None
    company: dict


# =======================================================
# MEMBERS
# =======================================================

class PublicMemberItem(BaseModel):
    id_company: str
    name: str
    description: Optional[str] = None
    media_logo_rectangle_id: Optional[str] = None


class PublicMembersResponse(BaseModel):
    items: List[PublicMemberItem]


class PublicMemberNewsItem(BaseModel):
    id_news: str
    title: str
    excerpt: Optional[str] = None
    published_at: datetime


class PublicMemberResponse(BaseModel):
    id_company: str
    name: str
    description: Optional[str] = None
    media_logo_rectangle_id: Optional[str] = None
    news: List[PublicMemberNewsItem]


# =======================================================
# NEWSLETTER
# =======================================================

class NewsletterSubscribeRequest(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    topics: Optional[List[str]] = None


class NewsletterSubscribeResponse(BaseModel):
    success: bool
