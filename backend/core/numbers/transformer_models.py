from datetime import datetime
from typing import (
    List,
    Literal,
    Optional,
)

from pydantic import (
    BaseModel,
    Field,
)


# ============================================================
# TYPES
# ============================================================

NumberTransformationStatus = Literal[
    "ACCEPTED",
    "REJECTED",
    "REVIEW",
]

NumberValueStatus = Literal[
    "ACTUAL",
    "ESTIMATE",
    "FORECAST",
    "TARGET",
    "UNKNOWN",
]

NumberEntityType = Literal[
    "company",
    "solution",
    "topic",
]


# ============================================================
# SOURCE ENTITY
# ============================================================

class NumberEntityCandidate(BaseModel):
    """
    One official GetCurator entity associated
    with the source content.

    The transformer may select entities only
    from this candidate list.
    """

    entity_type: NumberEntityType

    entity_id: str

    entity_label: str


# ============================================================
# CONTENT INPUT
# ============================================================

class NumberTransformationInput(BaseModel):
    """
    One content and its raw Numbers.

    This model is used only as input for the
    Numbers transformation pipeline.
    """

    id_content: str

    title: str

    excerpt: str = ""

    published_at: Optional[datetime] = None

    raw_numbers: List[str] = Field(
        default_factory=list,
    )

    entity_candidates: List[
        NumberEntityCandidate
    ] = Field(
        default_factory=list,
    )


# ============================================================
# TRANSFORMED ENTITY
# ============================================================

class TransformedNumberEntity(BaseModel):
    """
    One entity selected for one Number.

    entity_id must correspond to an entity
    supplied in entity_candidates.
    """

    entity_type: NumberEntityType

    entity_id: str

    entity_label: str


# ============================================================
# TRANSFORMED NUMBER
# ============================================================

class TransformedNumber(BaseModel):
    """
    One Number after normalization, qualification
    and entity dispatch.
    """

    # Original line, preserved exactly
    raw_line: str

    # Transformation decision
    status: NumberTransformationStatus

    # Human-readable normalized metric
    label: Optional[str] = None

    # Stable semantic family
    metric_type: Optional[str] = None

    # Single numeric value
    value: Optional[float] = None

    # Optional range
    value_min: Optional[float] = None
    value_max: Optional[float] = None

    # Canonical measurement representation
    unit: Optional[str] = None
    scale: Optional[str] = None

    # Geographic and temporal dimensions
    zone: Optional[str] = None
    period_label: Optional[str] = None

    # Actual / estimate / forecast / target
    value_status: NumberValueStatus = "UNKNOWN"

    # Official GetCurator entities
    entities: List[
        TransformedNumberEntity
    ] = Field(
        default_factory=list,
    )

    # Score between 0 and 1
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    # Explanation for REVIEW or REJECTED
    reason: Optional[str] = None


# ============================================================
# TRANSFORMATION RESULT
# ============================================================

class NumberTransformationResult(BaseModel):
    """
    Complete preview result for one content.
    """

    id_content: str

    title: str

    published_at: Optional[datetime] = None

    raw_numbers_count: int

    accepted_count: int

    rejected_count: int

    review_count: int

    numbers: List[
        TransformedNumber
    ] = Field(
        default_factory=list,
    )
