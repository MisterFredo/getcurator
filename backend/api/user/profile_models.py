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

EntityType = Literal[
    "company",
    "solution",
    "topic",
    "concept",
]

EntityResolutionStatus = Literal[
    "PENDING",
    "RESOLVED",
    "UNRESOLVED",
]

WatchPriority = Literal[
    "CORE",
    "WATCH",
]

WatchHorizon = Literal[
    "CURRENT",
    "FUTURE",
]

DecisionPriority = Literal[
    "HIGH",
    "MEDIUM",
    "LOW",
]


# ============================================================
# BASE MODEL
# ============================================================

class StrictProfileModel(
    BaseModel,
):

    class Config:

        extra = "forbid"


# ============================================================
# ENTITY REFERENCE
# ============================================================

class ProfileEntityReference(
    StrictProfileModel,
):

    label: str = Field(
        ...,
        description=(
            "Entity name exactly as understood "
            "from the user profile."
        ),
    )

    entity_type: EntityType = Field(
        ...,
        description=(
            "Expected entity type."
        ),
    )

    canonical_label: Optional[str] = Field(
        default=None,
        description=(
            "Canonical entity name after backend resolution."
        ),
    )

    entity_id: Optional[str] = Field(
        default=None,
        description=(
            "Canonical database identifier after resolution."
        ),
    )

    resolution_status: EntityResolutionStatus = Field(
        default="PENDING",
        description=(
            "Entity resolution status."
        ),
    )


# ============================================================
# PROFESSIONAL CONTEXT
# ============================================================

class ProfileProfessionalContext(
    StrictProfileModel,
):

    job_title: Optional[str] = None

    company: Optional[str] = None

    group: Optional[str] = None

    industries: List[str] = Field(
        default_factory=list,
    )

    functions: List[str] = Field(
        default_factory=list,
    )


# ============================================================
# GEOGRAPHICAL SCOPE
# ============================================================

class ProfileGeographicalScope(
    StrictProfileModel,
):

    current: List[str] = Field(
        default_factory=list,
        description=(
            "Markets explicitly described as currently active."
        ),
    )

    priority: List[str] = Field(
        default_factory=list,
        description=(
            "Markets explicitly described as priorities."
        ),
    )

    expansion: List[str] = Field(
        default_factory=list,
        description=(
            "Markets associated with launches or expansion."
        ),
    )


# ============================================================
# WATCH INSTRUCTION
# ============================================================

class ProfileWatchInstruction(
    StrictProfileModel,
):

    label: str = Field(
        ...,
        description=(
            "Short label describing the watch area."
        ),
    )

    instruction: str = Field(
        ...,
        description=(
            "Complete natural-language watch instruction "
            "preserving the user's intent."
        ),
    )

    priority: WatchPriority = Field(
        default="CORE",
    )

    horizon: WatchHorizon = Field(
        default="CURRENT",
    )

    horizon_label: Optional[str] = Field(
        default=None,
        description=(
            "Explicit horizon from the profile, "
            "for example '2027+'."
        ),
    )

    entities: List[ProfileEntityReference] = Field(
        default_factory=list,
    )

    topics: List[str] = Field(
        default_factory=list,
    )

    concepts: List[str] = Field(
        default_factory=list,
    )

    keywords: List[str] = Field(
        default_factory=list,
    )

    geographies: ProfileGeographicalScope = Field(
        default_factory=ProfileGeographicalScope,
    )


# ============================================================
# DECISION LENS
# ============================================================

class ProfileDecisionLens(
    StrictProfileModel,
):

    label: str = Field(
        ...,
        description=(
            "Short label describing the strategic priority."
        ),
    )

    instruction: str = Field(
        ...,
        description=(
            "Natural-language criterion used to evaluate "
            "whether content matters to the user."
        ),
    )

    priority: DecisionPriority = Field(
        default="HIGH",
    )

    topics: List[str] = Field(
        default_factory=list,
    )

    concepts: List[str] = Field(
        default_factory=list,
    )

    metrics: List[str] = Field(
        default_factory=list,
    )

    keywords: List[str] = Field(
        default_factory=list,
    )

    related_entities: List[ProfileEntityReference] = Field(
        default_factory=list,
    )


# ============================================================
# NEGATIVE PREFERENCE
# ============================================================

class ProfileNegativePreference(
    StrictProfileModel,
):

    instruction: str = Field(
        ...,
        description=(
            "Content the user explicitly describes "
            "as irrelevant or low priority."
        ),
    )

    content_types: List[str] = Field(
        default_factory=list,
    )

    topics: List[str] = Field(
        default_factory=list,
    )

    keywords: List[str] = Field(
        default_factory=list,
    )

    exceptions: List[str] = Field(
        default_factory=list,
        description=(
            "Conditions under which the content may "
            "still be relevant."
        ),
    )


# ============================================================
# STRUCTURED USER PROFILE
# ============================================================

class StructuredUserProfile(
    StrictProfileModel,
):

    schema_version: str = Field(
        default="1.0",
    )

    language: Literal[
        "fr",
        "en",
    ] = Field(
        default="fr",
    )

    professional_context: ProfileProfessionalContext = Field(
        default_factory=ProfileProfessionalContext,
    )

    watch_instructions: List[ProfileWatchInstruction] = Field(
        default_factory=list,
        description=(
            "Instructions used to expand the initial "
            "content preselection."
        ),
    )

    decision_lenses: List[ProfileDecisionLens] = Field(
        default_factory=list,
        description=(
            "Strategic criteria used to rank the candidates."
        ),
    )

    negative_preferences: List[ProfileNegativePreference] = Field(
        default_factory=list,
        description=(
            "Explicitly unwanted or low-value content."
        ),
    )


# ============================================================
# TRANSFORMER RESULT
# ============================================================

class ProfileTransformerResult(
    StrictProfileModel,
):

    structured_profile: StructuredUserProfile

    source_hash: str

    schema_version: str

    transformer_version: str

    warnings: List[str] = Field(
        default_factory=list,
    )
