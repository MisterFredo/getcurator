from dataclasses import dataclass, field
from typing import Any


# ============================================================
# PROFILE
# ============================================================

@dataclass
class ExpertiseProfile:

    id: str

    language: str

    preferences: dict

    keywords: list[str]

    geographies: list[str]

    profile_text: str


# ============================================================
# CONTENT
# ============================================================

@dataclass
class ExpertiseContent:

    id: str

    title: str

    excerpt: str

    published_at: Any

    url: str

    primary_company_logo: str | None

    companies: list

    solutions: list

    topics: list

    universes: list

    concepts: list


# ============================================================
# CONTEXT
# ============================================================

@dataclass
class ExpertiseContext:

    profile: ExpertiseProfile

    contents: list[ExpertiseContent]

    count: int = 0


# ============================================================
# INSIGHTS
# ============================================================

@dataclass
class ExpertiseInsights:

    summary: str = ""

    implications: str = ""


# ============================================================
# RESULT
# ============================================================

@dataclass
class Expertise:

    context: ExpertiseContext

    insights: ExpertiseInsights
