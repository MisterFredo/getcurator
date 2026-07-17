# backend/api/expertise/models.py

from typing import Any

from pydantic import BaseModel, Field


# ============================================================
# PREFERENCES
# ============================================================

class ExpertisePreferences(BaseModel):

    companies: list[str] = Field(
        default_factory=list,
    )

    solutions: list[str] = Field(
        default_factory=list,
    )

    topics: list[str] = Field(
        default_factory=list,
    )


# ============================================================
# PROFILE
# ============================================================

class ExpertiseProfile(BaseModel):

    id: str

    language: str

    preferences: ExpertisePreferences = Field(
        default_factory=ExpertisePreferences,
    )

    keywords: list[str] = Field(
        default_factory=list,
    )

    geographies: list[str] = Field(
        default_factory=list,
    )

    profile_text: str = ""


# ============================================================
# CONTENT
# ============================================================

class ExpertiseContent(BaseModel):

    id: str

    title: str

    excerpt: str

    published_at: Any

    url: str

    primary_company_logo: str | None = None

    companies: list[dict] = Field(
        default_factory=list,
    )

    solutions: list[dict] = Field(
        default_factory=list,
    )

    topics: list[dict] = Field(
        default_factory=list,
    )

    universes: list[dict] = Field(
        default_factory=list,
    )

    concepts: list[dict] = Field(
        default_factory=list,
    )


# ============================================================
# CONTEXT
# ============================================================

class ExpertiseContext(BaseModel):

    profile: ExpertiseProfile

    contents: list[ExpertiseContent] = Field(
        default_factory=list,
    )

    count: int = 0


# ============================================================
# INSIGHTS
# ============================================================

class ExpertiseInsights(BaseModel):

    summary: str = ""

    implications: str = ""


# ============================================================
# EXPERTISE
# ============================================================

class Expertise(BaseModel):

    profile: ExpertiseProfile

    contents: list[ExpertiseContent] = Field(
        default_factory=list,
    )

    count: int = 0

    summary: str = ""

    implications: str = ""
