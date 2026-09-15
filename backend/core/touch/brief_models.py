from typing import (
    Literal,
)

from pydantic import (
    BaseModel,
    Field,
)

from core.touch.notebook_models import (
    TouchCorpusNotebook,
)


# ============================================================
# TYPES
# ============================================================

TouchBriefType = Literal[
    "STRATEGIC_EVENT",
    "COMPARATIVE",
    "CHRONOLOGICAL",
    "PEDAGOGICAL",
    "MARKET_ANALYSIS",
    "HYBRID",
]


TouchBriefTypeRequest = Literal[
    "AUTO",
    "STRATEGIC_EVENT",
    "COMPARATIVE",
    "CHRONOLOGICAL",
    "PEDAGOGICAL",
    "MARKET_ANALYSIS",
    "HYBRID",
]


TouchBriefSectionType = Literal[
    "ESSENTIAL",
    "EXPLANATION",
    "MECHANISM",
    "ACTOR_READING",
    "COMPARISON",
    "TIMELINE",
    "MARKET_DYNAMICS",
    "TENSIONS",
    "KEY_NUMBERS",
    "EXAMPLES",
    "OPEN_QUESTIONS",
    "OTHER",
]


TouchBriefSectionLayout = Literal[
    "BULLETS",
    "STEPS",
    "COLUMNS",
    "TIMELINE",
    "NUMBER_CARDS",
]


TouchBriefStatus = Literal[
    "GENERATED",
    "GENERATION_FAILED",
]


# ============================================================
# STRICT MODEL
# ============================================================

class StrictTouchBriefModel(
    BaseModel,
):

    class Config:

        extra = "forbid"


# ============================================================
# SECTION GROUP
# ============================================================

class TouchBriefSectionGroup(
    StrictTouchBriefModel,
):

    label: str

    note_ids: list[str] = Field(
        default_factory=list,
    )

    number_ids: list[str] = Field(
        default_factory=list,
    )

    event_ids: list[str] = Field(
        default_factory=list,
    )


# ============================================================
# BRIEF SECTION
# ============================================================

class TouchBriefSection(
    StrictTouchBriefModel,
):

    section_id: str

    section_type: TouchBriefSectionType

    title: str

    introduction: str = ""

    layout: TouchBriefSectionLayout

    note_ids: list[str] = Field(
        default_factory=list,
    )

    number_ids: list[str] = Field(
        default_factory=list,
    )

    event_ids: list[str] = Field(
        default_factory=list,
    )

    groups: list[
        TouchBriefSectionGroup
    ] = Field(
        default_factory=list,
    )


# ============================================================
# BRIEF STRUCTURE
# ============================================================

class TouchBriefStructure(
    StrictTouchBriefModel,
):

    brief_type: TouchBriefType

    secondary_brief_type: TouchBriefType | None = None

    recommendation_reason: str

    headline: str

    subheadline: str

    central_question: str

    key_message: str

    sections: list[
        TouchBriefSection
    ] = Field(
        default_factory=list,
    )

    hidden_note_ids: list[str] = Field(
        default_factory=list,
    )

    hidden_number_ids: list[str] = Field(
        default_factory=list,
    )

    editorial_cautions: list[str] = Field(
        default_factory=list,
    )


# ============================================================
# REQUEST
# ============================================================

class TouchBriefRequest(
    StrictTouchBriefModel,
):

    notebook: TouchCorpusNotebook

    requested_brief_type: TouchBriefTypeRequest = "AUTO"

    editorial_instruction: str = ""

    output_language: str = "fr"


# ============================================================
# OUTCOME
# ============================================================

class TouchBriefOutcome(
    StrictTouchBriefModel,
):

    status: TouchBriefStatus

    brief: TouchBriefStructure | None = None

    error: str | None = None
