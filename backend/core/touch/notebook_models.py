from datetime import (
    date,
)

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

TouchEvidenceNoteType = Literal[
    "FACT",
    "MECHANISM",
    "NUMBER",
    "STRATEGIC_READING",
    "TENSION",
    "LIMITATION",
    "UNCERTAINTY",
    "COMPARISON",
    "MILESTONE",
    "EXAMPLE",
]


TouchEvidenceConfidence = Literal[
    "HIGH",
    "MEDIUM",
    "LOW",
]


TouchEvidenceStatus = Literal[
    "VALIDATED",
    "TO_VERIFY",
    "CONTRADICTED",
]


TouchGenerationStatus = Literal[
    "GENERATED",
    "GENERATION_FAILED",
]


# ============================================================
# STRICT MODEL
# ============================================================

class StrictTouchNotebookModel(
    BaseModel,
):

    class Config:

        extra = "forbid"


# ============================================================
# NOTE
# ============================================================

class TouchEvidenceNote(
    StrictTouchNotebookModel,
):

    note_id: str

    note_type: TouchEvidenceNoteType

    statement: str

    explanation: str = ""

    actors: list[str] = Field(
        default_factory=list,
    )

    geographies: list[str] = Field(
        default_factory=list,
    )

    dates: list[str] = Field(
        default_factory=list,
    )

    confidence: TouchEvidenceConfidence

    status: TouchEvidenceStatus = (
        "VALIDATED"
    )

    source_content_ids: list[str] = Field(
        default_factory=list,
    )


# ============================================================
# EVENT
# ============================================================

class TouchNotebookEvent(
    StrictTouchNotebookModel,
):

    event_id: str

    title: str

    description: str

    event_date: str | None = None

    actors: list[str] = Field(
        default_factory=list,
    )

    note_ids: list[str] = Field(
        default_factory=list,
    )

    source_content_ids: list[str] = Field(
        default_factory=list,
    )


# ============================================================
# TIMELINE ITEM
# ============================================================

class TouchNotebookTimelineItem(
    StrictTouchNotebookModel,
):

    date: str

    label: str

    description: str = ""

    event_id: str | None = None

    note_ids: list[str] = Field(
        default_factory=list,
    )

    source_content_ids: list[str] = Field(
        default_factory=list,
    )


# ============================================================
# VALIDATED NUMBER
# ============================================================

class TouchNotebookNumber(
    StrictTouchNotebookModel,
):

    number_id: str

    value: str

    unit: str

    metric: str

    context: str

    actor: str | None = None

    geography: str | None = None

    period: str | None = None

    confidence: TouchEvidenceConfidence

    note_ids: list[str] = Field(
        default_factory=list,
    )

    source_content_ids: list[str] = Field(
        default_factory=list,
    )


# ============================================================
# QUARANTINED NUMBER
# ============================================================

class TouchQuarantinedNumber(
    StrictTouchNotebookModel,
):

    value: str

    unit: str = ""

    metric: str = ""

    context: str = ""

    reason: str

    source_content_ids: list[str] = Field(
        default_factory=list,
    )


# ============================================================
# CONTRADICTION
# ============================================================

class TouchNotebookContradiction(
    StrictTouchNotebookModel,
):

    subject: str

    description: str

    note_ids: list[str] = Field(
        default_factory=list,
    )

    source_content_ids: list[str] = Field(
        default_factory=list,
    )

    resolution: str | None = None


# ============================================================
# COVERAGE DIMENSION
# ============================================================

class TouchNotebookDimension(
    StrictTouchNotebookModel,
):

    label: str

    summary: str

    note_ids: list[str] = Field(
        default_factory=list,
    )

    source_content_ids: list[str] = Field(
        default_factory=list,
    )


# ============================================================
# CORPUS NOTEBOOK
# ============================================================

class TouchCorpusNotebook(
    StrictTouchNotebookModel,
):

    subject: str

    objective: str

    corpus_summary: str

    notes: list[
        TouchEvidenceNote
    ] = Field(
        default_factory=list,
    )

    events: list[
        TouchNotebookEvent
    ] = Field(
        default_factory=list,
    )

    timeline: list[
        TouchNotebookTimelineItem
    ] = Field(
        default_factory=list,
    )

    dimensions: list[
        TouchNotebookDimension
    ] = Field(
        default_factory=list,
    )

    validated_numbers: list[
        TouchNotebookNumber
    ] = Field(
        default_factory=list,
    )

    quarantined_numbers: list[
        TouchQuarantinedNumber
    ] = Field(
        default_factory=list,
    )

    contradictions: list[
        TouchNotebookContradiction
    ] = Field(
        default_factory=list,
    )

    corpus_strengths: list[str] = Field(
        default_factory=list,
    )

    corpus_limits: list[str] = Field(
        default_factory=list,
    )


# ============================================================
# REQUEST
# ============================================================

class TouchNotebookRequest(
    StrictTouchNotebookModel,
):

    subject: str

    objective: str = ""

    content_ids: list[str] = Field(
        ...,
        min_length=1,
    )

    output_language: str = "fr"


# ============================================================
# OUTCOME
# ============================================================

class TouchNotebookOutcome(
    StrictTouchNotebookModel,
):

    status: TouchGenerationStatus

    notebook: TouchCorpusNotebook | None = None

    source_count: int = 0

    error: str | None = None
