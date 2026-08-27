from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Literal
from datetime import datetime, date

# ============================================================
# CREATE
# ============================================================

class ContentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # ========================================================
    # META
    # ========================================================
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

# ============================================================
# UPDATE
# ============================================================

class ContentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # ========================================================
    # META
    # ========================================================
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
    content_body_en: Optional[str] = None

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
    mecanique_expliquee_en: Optional[str] = None

    enjeu_strategique: Optional[str] = None
    enjeu_strategique_en: Optional[str] = None

    point_de_friction: Optional[str] = None
    point_de_friction_en: Optional[str] = None

    signal_analytique: Optional[str] = None
    signal_analytique_en: Optional[str] = None


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
    content_body_en: Optional[str] = None

    source_date: Optional[date] = None

    chiffres: List[str] = Field(default_factory=list)

    acteurs_cites: List[str] = Field(default_factory=list)

    mecanique_expliquee: Optional[str] = None
    mecanique_expliquee_en: Optional[str] = None

    enjeu_strategique: Optional[str] = None
    enjeu_strategique_en: Optional[str] = None

    point_de_friction: Optional[str] = None
    point_de_friction_en: Optional[str] = None

    signal_analytique: Optional[str] = None
    signal_analytique_en: Optional[str] = None
    concepts_llm: List[str] = Field(default_factory=list)
    solutions_llm: List[str] = Field(default_factory=list)
    topics_llm: List[str] = Field(default_factory=list)

    published_at: Optional[datetime] = None


# ============================================================
# CONTENT LIST
# ============================================================

class ContentFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    search: Optional[str] = None

    company_id: Optional[str] = None
    solution_id: Optional[str] = None
    topic_id: Optional[str] = None
    concept_id: Optional[str] = None
    source_id: Optional[str] = None

    date_from: Optional[date] = None
    date_to: Optional[date] = None

    only_numbers: bool = False


class ContentListRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filters: ContentFilters = Field(
        default_factory=ContentFilters,
    )

    page: int = Field(
        default=1,
        ge=1,
    )

    page_size: int = Field(
        default=100,
        ge=1,
        le=500,
    )


class ContentListItem(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    id_content: str

    id_primary_company: Optional[str] = None

    primary_company_name: Optional[str] = None

    source_url: Optional[str] = None

    source_title: Optional[str] = None

    title: Optional[str] = None

    title_en: Optional[str] = None

    excerpt: Optional[str] = None

    excerpt_en: Optional[str] = None

    status: Optional[str] = None

    translation_status: Optional[
        Literal[
            "MISSING",
            "PARTIAL",
            "COMPLETE",
        ]
    ] = None

    translation_required_count: int = 0

    translation_completed_count: int = 0

    source_date: Optional[date] = None

    published_at: Optional[datetime] = None

    updated_at: Optional[datetime] = None

class ContentListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contents: List[ContentListItem]

    total_results: int

    page: int

    page_size: int

    total_pages: int

class BulkIdsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ids: List[str]


# ============================================================
# SEARCH
# ============================================================

class ContentSearchFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    search: Optional[str] = None

    status: Optional[
        Literal[
            "DRAFT",
            "READY",
            "SCHEDULED",
            "PUBLISHED",
        ]
    ] = None

    company_id: Optional[str] = None
    solution_id: Optional[str] = None
    topic_id: Optional[str] = None
    concept_id: Optional[str] = None
    source_id: Optional[str] = None

    date_from: Optional[date] = None
    date_to: Optional[date] = None

    only_numbers: bool = False


class ContentSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filters: ContentSearchFilters = Field(
        default_factory=ContentSearchFilters
    )

    page: int = Field(
        default=1,
        ge=1,
    )

    page_size: int = Field(
        default=100,
        ge=1,
        le=500,
    )


class ContentSearchItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id_content: str

    title: Optional[str] = None

    source_title: Optional[str] = None

    source_date: Optional[date] = None

    published_at: Optional[datetime] = None


class ContentSearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contents: List[ContentSearchItem]

    total_results: int

    page: int

    page_size: int

    total_pages: int
