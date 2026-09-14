from typing import (
    Literal,
)

from pydantic import (
    BaseModel,
    Field,
)


# ============================================================
# TYPES
# ============================================================

TouchDraftStatus = Literal[
    "GENERATED",
    "GENERATION_FAILED",
]


TouchSectionType = Literal[
    "WHAT_HAPPENED",
    "WHY_IT_MATTERS",
    "HOW_IT_WORKS",
    "BIGGER_PICTURE",
]


# ============================================================
# STRICT MODEL
# ============================================================

class StrictTouchGenerationModel(
    BaseModel,
):

    class Config:

        extra = "forbid"


# ============================================================
# GENERATION REQUEST
# ============================================================

class TouchGenerationRequest(
    StrictTouchGenerationModel,
):

    subject: str

    objective: str = ""

    output_language: str = "fr"

    content_ids: list[str] = Field(
        ...,
        min_length=1,
    )


# ============================================================
# NARRATIVE SECTION
# ============================================================

class TouchNarrativeSection(
    StrictTouchGenerationModel,
):

    section_type: TouchSectionType

    title: str

    body: str

    source_content_ids: list[str] = Field(
        default_factory=list,
    )


# ============================================================
# EXECUTIVE TAKEAWAY
# ============================================================

class TouchExecutiveTakeaway(
    StrictTouchGenerationModel,
):

    statement: str

    source_content_ids: list[str] = Field(
        default_factory=list,
    )


# ============================================================
# WATCH POINT
# ============================================================

class TouchWatchPoint(
    StrictTouchGenerationModel,
):

    label: str

    explanation: str

    source_content_ids: list[str] = Field(
        default_factory=list,
    )


# ============================================================
# KEY NUMBER
# ============================================================

class TouchKeyNumber(
    StrictTouchGenerationModel,
):

    value: str

    label: str

    context: str

    source_content_ids: list[str] = Field(
        default_factory=list,
    )


# ============================================================
# SOURCE
# ============================================================

class TouchDocumentSource(
    StrictTouchGenerationModel,
):

    content_id: str

    title: str

    source_title: str = ""

    source_url: str = ""

    published_at: str | None = None


# ============================================================
# ONE-PAGER DRAFT
# ============================================================

class TouchOnePagerDraft(
    StrictTouchGenerationModel,
):

    title: str

    subtitle: str

    executive_takeaways: list[
        TouchExecutiveTakeaway
    ] = Field(
        default_factory=list,
    )

    sections: list[
        TouchNarrativeSection
    ] = Field(
        default_factory=list,
    )

    key_numbers: list[
        TouchKeyNumber
    ] = Field(
        default_factory=list,
    )

    what_to_watch: list[
        TouchWatchPoint
    ] = Field(
        default_factory=list,
    )


# ============================================================
# GENERATION OUTCOME
# ============================================================

class TouchGenerationOutcome(
    StrictTouchGenerationModel,
):

    status: TouchDraftStatus

    draft: TouchOnePagerDraft | None = None

    sources: list[
        TouchDocumentSource
    ] = Field(
        default_factory=list,
    )

    error: str | None = None
