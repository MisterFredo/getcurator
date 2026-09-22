from datetime import datetime

from typing import (
    Literal,
    get_args,
)

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


# ============================================================
# TYPES
# ============================================================

TouchEntityType = Literal[
    "company",
    "solution",
    "topic",
]


TouchCandidateSource = Literal[
    "CORE_COMPANY",
    "CORE_SOLUTION",
    "CORE_TOPIC",
    "SEARCH_TERM",
    "RELATED_ANGLE",
]


TouchContentRelevance = Literal[
    "DIRECT",
    "CONTEXT",
    "RELATED",
    "OUT_OF_SCOPE",
]


TouchCoverageDimension = Literal[
    "ANNOUNCEMENT",
    "ACTORS",
    "MECHANISM",
    "PRODUCT_SCOPE",
    "GEOGRAPHY",
    "TIMELINE",
    "BUSINESS_MODEL",
    "STRATEGY",
    "MARKET_CONTEXT",
    "NUMBERS",
    "REACTIONS",
    "LIMITATIONS",
    "OUTLOOK",
]

ALLOWED_TOUCH_COVERAGE_DIMENSIONS = set(
    get_args(TouchCoverageDimension)
)


def _valid_coverage_dimensions(value):
    if not isinstance(value, list):
        return value

    return [
        dimension
        for dimension in value
        if dimension in ALLOWED_TOUCH_COVERAGE_DIMENSIONS
    ]


TouchConversationRole = Literal[
    "user",
    "assistant",
]


# ============================================================
# STRICT MODEL
# ============================================================

class StrictTouchSearchModel(
    BaseModel,
):

    class Config:

        extra = "forbid"


# ============================================================
# ENTITY REFERENCE
# ============================================================

class TouchEntityReference(
    StrictTouchSearchModel,
):

    entity_type: TouchEntityType

    entity_id: str

    entity_label: str


# ============================================================
# CONVERSATION MESSAGE
# ============================================================

class TouchConversationMessage(
    StrictTouchSearchModel,
):

    role: TouchConversationRole

    content: str



# ============================================================
# INTERPRETED RESEARCH QUERY
# ============================================================

class TouchResearchInterpretation(
    StrictTouchSearchModel,
):

    subject: str

    objective: str

    companies: list[
        TouchEntityReference
    ] = Field(
        default_factory=list,
    )

    solutions: list[
        TouchEntityReference
    ] = Field(
        default_factory=list,
    )

    topics: list[
        TouchEntityReference
    ] = Field(
        default_factory=list,
    )

    search_terms: list[str] = Field(
        default_factory=list,
    )

    related_angles: list[str] = Field(
        default_factory=list,
    )

    response_message: str = ""


# ============================================================
# RESEARCH BRIEF
# ============================================================

class TouchResearchBrief(
    StrictTouchSearchModel,
):

    query: str

    output_language: str = "fr"

    period_start: datetime | None = None

    period_end: datetime | None = None

    companies: list[
        TouchEntityReference
    ] = Field(
        default_factory=list,
    )

    solutions: list[
        TouchEntityReference
    ] = Field(
        default_factory=list,
    )

    topics: list[
        TouchEntityReference
    ] = Field(
        default_factory=list,
    )

    prepared_interpretation: (
        TouchResearchInterpretation
        | None
    ) = None

    conversation_history: list[
        TouchConversationMessage
    ] = Field(
        default_factory=list,
    )

    selected_content_ids: list[str] = Field(
        default_factory=list,
    )

    dismissed_content_ids: list[str] = Field(
        default_factory=list,
    )

    previously_proposed_content_ids: list[
        str
    ] = Field(
        default_factory=list,
    )

# ============================================================
# CONTENT CANDIDATE
# ============================================================

class TouchContentCandidate(
    StrictTouchSearchModel,
):

    content_id: str

    title: str

    excerpt: str = ""

    source_title: str = ""

    source_url: str = ""

    published_at: datetime | None = None

    content_body: str = ""

    signal_analytique: str = ""

    mecanique_expliquee: str = ""

    enjeu_strategique: str = ""

    point_de_friction: str = ""

    chiffres: list = Field(
        default_factory=list,
    )

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

    selection_sources: list[
        TouchCandidateSource
    ] = Field(
        default_factory=list,
    )

    matched_entities: list[str] = Field(
        default_factory=list,
    )

    matched_terms: list[str] = Field(
        default_factory=list,
    )

    matched_angles: list[str] = Field(
        default_factory=list,
    )


# ============================================================
# CONTENT DECISION
# ============================================================

class TouchContentDecision(
    StrictTouchSearchModel,
):

    content_id: str

    event_key: str | None = None

    relevance: TouchContentRelevance

    relevance_score: int = Field(
        ...,
        ge=0,
        le=100,
    )

    reason: str

    coverage_dimensions: list[
        TouchCoverageDimension
    ] = Field(
        default_factory=list,
    )

    @field_validator(
        "coverage_dimensions",
        mode="before",
    )
    @classmethod
    def validate_coverage_dimensions(
        cls,
        value,
    ):
        return _valid_coverage_dimensions(
            value
        )

    key_contributions: list[str] = Field(
        default_factory=list,
    )

    overlaps_with: list[str] = Field(
        default_factory=list,
    )

    contradictions_with: list[str] = Field(
        default_factory=list,
    )

# ============================================================
# CANDIDATE EVALUATION RESULT
# ============================================================

class TouchCandidateEvaluationResult(
    StrictTouchSearchModel,
):

    decisions: list[
        TouchContentDecision
    ] = Field(
        default_factory=list,
    )


# ============================================================
# EVENT GROUP
# ============================================================

class TouchEventGroup(
    StrictTouchSearchModel,
):

    event_key: str

    label: str

    content_ids: list[str] = Field(
        default_factory=list,
    )

    shared_information: list[str] = Field(
        default_factory=list,
    )

    complementary_contributions: list[str] = Field(
        default_factory=list,
    )

    contradictions: list[str] = Field(
        default_factory=list,
    )


# ============================================================
# COVERAGE ANALYSIS
# ============================================================

class TouchCoverageAnalysis(
    StrictTouchSearchModel,
):

    summary: str = ""

    covered_dimensions: list[
        TouchCoverageDimension
    ] = Field(
        default_factory=list,
    )

    missing_dimensions: list[
        TouchCoverageDimension
    ] = Field(
        default_factory=list,
    )

    strengths: list[str] = Field(
        default_factory=list,
    )

    gaps: list[str] = Field(
        default_factory=list,
    )

    contradictions: list[str] = Field(
        default_factory=list,
    )

    suggested_follow_ups: list[str] = Field(
        default_factory=list,
    )


# ============================================================
# CONSOLIDATION RESULT
# ============================================================

class TouchConsolidationResult(
    StrictTouchSearchModel,
):

    event_groups: list[
        TouchEventGroup
    ] = Field(
        default_factory=list,
    )

    coverage_analysis: TouchCoverageAnalysis = Field(
        default_factory=TouchCoverageAnalysis,
    )


# ============================================================
# SEARCH OUTCOME
# ============================================================

class TouchSearchOutcome(
    StrictTouchSearchModel,
):

    interpretation: TouchResearchInterpretation

    candidates: list[
        TouchContentCandidate
    ] = Field(
        default_factory=list,
    )

    evaluation: TouchCandidateEvaluationResult = Field(
        default_factory=(
            TouchCandidateEvaluationResult
        ),
    )

    consolidation: TouchConsolidationResult = Field(
        default_factory=(
            TouchConsolidationResult
        ),
    )

    used_fallback: bool = False

    errors: list[str] = Field(
        default_factory=list,
    )
