from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Literal
from datetime import datetime, date


# ============================================================
# PERSON LINK (avec rôle)
# ============================================================

class ContentPerson(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id_person: str
    role: Optional[str] = None


# ============================================================
# IA — SUMMARY REQUEST
# ============================================================

class ContentSummaryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: Optional[str] = None
    source_text: str
    content_type: Literal["ANALYSIS", "NEWS"] = "ANALYSIS"
    id_primary_company: Optional[str] = None


# ============================================================
# RAW — STORE
# ============================================================

class ContentRawCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content_type: Literal[
        "ANALYSIS",
        "NEWS"
    ] = "ANALYSIS"

    source_id: str
    source_title: str
    source_url: Optional[str] = None
    discovery_id: Optional[str] = None
    raw_text: str

    date_source: Optional[date] = None

    # 🔥 NEW
    id_primary_company: Optional[str] = None


class ContentRawUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content_type: Optional[
        Literal["ANALYSIS", "NEWS"]
    ] = None

    # 🔥 NEW
    id_primary_company: Optional[str] = None

    source_title: Optional[str] = None
    source_url: Optional[str] = None
    date_source: Optional[date] = None
    raw_text: Optional[str] = None


class ContentRawOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id_raw: str

    content_type: Literal[
        "ANALYSIS",
        "NEWS"
    ] = "ANALYSIS"

    source_id: str
    source_url: Optional[str] = None
    source_title: str

    # 🔥 NEW
    id_primary_company: Optional[str] = None

    date_source: Optional[date] = None

    status: str
    created_at: datetime


class ContentRawDestockRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id_raw: Optional[str] = None
    limit: int = 20


class BulkIdsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ids: List[str]


class ImportUrlsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    urls_text: str

    id_source: str

    content_type: Literal[
        "ANALYSIS",
        "NEWS"
    ] = "ANALYSIS"

    id_primary_company: Optional[str] = None

class ImportCsvRequest(BaseModel):
    csv_text: str
    id_source: str
    content_type: str = "ANALYSIS"


# ============================================================
# CREATE
# ============================================================

class ContentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # ========================================================
    # META
    # ========================================================

    content_type: Literal[
        "ANALYSIS",
        "NEWS"
    ] = "ANALYSIS"

    # 🔥 NEW
    id_primary_company: Optional[str] = None

    # 🔥 NEW
    id_raw: Optional[str] = None

    # ========================================================
    # SOURCE
    # ========================================================

    source_id: Optional[str] = None
    source_text: Optional[str] = None

    # 🔥 EXISTING
    source_url: Optional[str] = None

    # 🔥 NEW
    source_title: Optional[str] = None

    source_author: Optional[str] = None

    source_published_at: Optional[date] = None
    source_date: Optional[date] = None

    # ========================================================
    # SUMMARY VALIDÉ
    # ========================================================

    title: str

    excerpt: Optional[str] = None
    content_body: Optional[str] = None

    # ========================================================
    # EXTRACTIONS STRUCTURÉES
    # ========================================================

    chiffres: List[str] = Field(default_factory=list)

    acteurs_cites: List[str] = Field(default_factory=list)

    concepts_llm: List[str] = Field(default_factory=list)

    solutions_llm: List[str] = Field(default_factory=list)

    topics_llm: List[str] = Field(default_factory=list)

    # ========================================================
    # ANALYSE STRATÉGIQUE
    # ========================================================

    mecanique_expliquee: Optional[str] = None

    enjeu_strategique: Optional[str] = None

    point_de_friction: Optional[str] = None

    signal_analytique: Optional[str] = None

    # ========================================================
    # ENTITÉS MÉTIER
    # ========================================================

    topics: List[str] = Field(default_factory=list)

    events: List[str] = Field(default_factory=list)

    companies: List[str] = Field(default_factory=list)

    persons: List[ContentPerson] = Field(default_factory=list)

    # ========================================================
    # TAGGING ANALYTIQUE
    # ========================================================

    concepts: List[str] = Field(default_factory=list)

    solutions: List[str] = Field(default_factory=list)

    # ========================================================
    # SEO
    # ========================================================

    seo_title: Optional[str] = None
    seo_description: Optional[str] = None

    # ========================================================
    # META
    # ========================================================

    author: Optional[str] = None

# ============================================================
# UPDATE
# ============================================================

class ContentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # ========================================================
    # META
    # ========================================================

    content_type: Optional[
        Literal["ANALYSIS", "NEWS"]
    ] = None

    # 🔥 NEW
    id_primary_company: Optional[str] = None

    # ========================================================
    # SOURCE
    # ========================================================

    source_id: Optional[str] = None
    source_text: Optional[str] = None
    source_url: Optional[str] = None
    source_author: Optional[str] = None

    source_published_at: Optional[date] = None
    source_date: Optional[date] = None

    # ========================================================
    # SUMMARY
    # ========================================================

    title: Optional[str] = None
    title_en: Optional[str] = None
    excerpt: Optional[str] = None
    excerpt_en: Optional[str] = None
    content_body: Optional[str] = None

    # ========================================================
    # EXTRACTIONS STRUCTURÉES
    # ========================================================

    chiffres: Optional[List[str]] = None
    acteurs_cites: Optional[List[str]] = None

    concepts_llm: Optional[List[str]] = None
    solutions_llm: Optional[List[str]] = None
    topics_llm: Optional[List[str]] = None

    # ========================================================
    # ANALYSE STRATÉGIQUE
    # ========================================================

    mecanique_expliquee: Optional[str] = None
    enjeu_strategique: Optional[str] = None
    point_de_friction: Optional[str] = None
    signal_analytique: Optional[str] = None

    # ========================================================
    # ENTITÉS MÉTIER
    # ========================================================

    topics: Optional[List[str]] = None
    events: Optional[List[str]] = None
    companies: Optional[List[str]] = None

    persons: Optional[
        List[ContentPerson]
    ] = None

    # ========================================================
    # TAGGING ANALYTIQUE
    # ========================================================

    concepts: Optional[List[str]] = None
    solutions: Optional[List[str]] = None

    # ========================================================
    # SEO
    # ========================================================

    seo_title: Optional[str] = None
    seo_description: Optional[str] = None

    # ========================================================
    # META
    # ========================================================

    author: Optional[str] = None


# ============================================================
# PUBLISH
# ============================================================

class ContentPublish(BaseModel):
    model_config = ConfigDict(extra="forbid")

    publish_at: Optional[datetime] = None


# ============================================================
# OUT
# ============================================================

class ContentOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id_content: str

    content_type: Literal[
        "ANALYSIS",
        "NEWS"
    ] = "ANALYSIS"

    # 🔥 NEW
    id_primary_company: Optional[str] = None

    status: str

    source_id: Optional[str] = None
    source_url: Optional[str] = None
    source_author: Optional[str] = None

    source_published_at: Optional[date] = None

    title: Optional[str] = None
    title_en: Optional[str] = None
    excerpt: Optional[str] = None
    excerpt_en: Optional[str] = None
    content_body: Optional[str] = None

    source_date: Optional[date] = None

    chiffres: List[str] = Field(default_factory=list)

    acteurs_cites: List[str] = Field(default_factory=list)

    mecanique_expliquee: Optional[str] = None
    enjeu_strategique: Optional[str] = None
    point_de_friction: Optional[str] = None
    signal_analytique: Optional[str] = None

    concepts_llm: List[str] = Field(default_factory=list)
    solutions_llm: List[str] = Field(default_factory=list)
    topics_llm: List[str] = Field(default_factory=list)

    published_at: Optional[datetime] = None

    topics: List[str] = Field(default_factory=list)
    events: List[str] = Field(default_factory=list)
    companies: List[str] = Field(default_factory=list)

    persons: List[ContentPerson] = Field(default_factory=list)

    concepts: List[str] = Field(default_factory=list)
    solutions: List[str] = Field(default_factory=list)
