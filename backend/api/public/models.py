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



