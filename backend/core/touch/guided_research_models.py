from datetime import datetime

from typing import Literal

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)

from core.touch.search_models import (
    TouchConversationMessage,
    TouchEntityReference,
)


# ============================================================
# TYPES
# ============================================================

TouchGuidedResearchAction = Literal[
    "START",
    "ANSWER",
    "PREPARE_PLAN",
    "REVISE",
]

TouchGuidedResearchPhase = Literal[
    "INTERVIEW",
    "PLAN_READY",
]

TouchGuidedResearchType = Literal[
    "ENTITY",
    "COMPARATIVE",
    "CROSS_SECTOR",
    "TOPIC",
    "EVOLUTION",
    "EVENT",
    "MARKET",
    "OTHER",
]

TouchGuidedEntityType = Literal[
    "company",
    "solution",
    "topic",
]

TouchGuidedEntityRole = Literal[
    "PRIMARY",
    "COMPARISON",
    "CONTEXT",
]

TouchGuidedAxisType = Literal[
    "CORE_SUBJECT",
    "COMPARISON",
    "CONTEXT",
    "MECHANISM",
    "EVIDENCE",
    "LIMITATIONS",
    "EVOLUTION",
    "OTHER",
]


# ============================================================
# ENTITY MENTION
# ============================================================

class TouchGuidedEntityMention(BaseModel):

    entity_type: TouchGuidedEntityType

    entity_label: str

    research_role: TouchGuidedEntityRole

    reason: str = ""

    confidence: float = 1.0

    @field_validator(
        "entity_label",
        "reason",
        mode="before",
    )
    @classmethod
    def normalize_text(
        cls,
        value,
    ) -> str:

        if not isinstance(
            value,
            str,
        ):
            return ""

        return value.strip()

    @field_validator(
        "confidence",
        mode="before",
    )
    @classmethod
    def normalize_confidence(
        cls,
        value,
    ) -> float:

        try:

            confidence = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            confidence = 0.0

        return max(
            0.0,
            min(
                1.0,
                confidence,
            ),
        )


# ============================================================
# RESEARCH AXIS
# ============================================================

class TouchGuidedResearchAxis(BaseModel):

    axis_id: str

    axis_type: TouchGuidedAxisType

    label: str

    objective: str

    search_terms: list[str] = Field(
        default_factory=list,
    )

    related_angles: list[str] = Field(
        default_factory=list,
    )

    @field_validator(
        "axis_id",
        "label",
        "objective",
        mode="before",
    )
    @classmethod
    def normalize_required_text(
        cls,
        value,
    ) -> str:

        if not isinstance(
            value,
            str,
        ):
            return ""

        return value.strip()

    @field_validator(
        "search_terms",
        "related_angles",
        mode="before",
    )
    @classmethod
    def normalize_text_list(
        cls,
        value,
    ) -> list[str]:

        if not isinstance(
            value,
            list,
        ):
            return []

        normalized_values = []

        seen_values = set()

        for item in value:

            if not isinstance(
                item,
                str,
            ):
                continue

            cleaned_item = (
                item.strip()
            )

            if not cleaned_item:
                continue

            key = (
                cleaned_item.casefold()
            )

            if key in seen_values:
                continue

            seen_values.add(
                key
            )

            normalized_values.append(
                cleaned_item
            )

        return normalized_values


# ============================================================
# GUIDED RESEARCH PLAN
# ============================================================

class TouchGuidedResearchPlan(BaseModel):

    subject: str = ""

    objective: str = ""

    central_question: str = ""

    research_type: TouchGuidedResearchType = (
        "OTHER"
    )

    scope_summary: str = ""

    target_context: str | None = None

    period_start: datetime | None = None

    period_end: datetime | None = None

    geographies: list[str] = Field(
        default_factory=list,
    )

    entity_mentions: list[
        TouchGuidedEntityMention
    ] = Field(
        default_factory=list,
    )

    resolved_entities: list[
        TouchEntityReference
    ] = Field(
        default_factory=list,
    )

    axes: list[
        TouchGuidedResearchAxis
    ] = Field(
        default_factory=list,
    )

    search_terms: list[str] = Field(
        default_factory=list,
    )

    related_angles: list[str] = Field(
        default_factory=list,
    )

    exclusions: list[str] = Field(
        default_factory=list,
    )

    assumptions: list[str] = Field(
        default_factory=list,
    )

    editorial_cautions: list[str] = Field(
        default_factory=list,
    )

    missing_information: list[str] = Field(
        default_factory=list,
    )

    ready_for_search: bool = False

    @field_validator(
        "subject",
        "objective",
        "central_question",
        "scope_summary",
        mode="before",
    )
    @classmethod
    def normalize_required_text(
        cls,
        value,
    ) -> str:

        if not isinstance(
            value,
            str,
        ):
            return ""

        return value.strip()

    @field_validator(
        "target_context",
        mode="before",
    )
    @classmethod
    def normalize_optional_text(
        cls,
        value,
    ) -> str | None:

        if not isinstance(
            value,
            str,
        ):
            return None

        cleaned_value = (
            value.strip()
        )

        return (
            cleaned_value
            or None
        )

    @field_validator(
        "geographies",
        "search_terms",
        "related_angles",
        "exclusions",
        "assumptions",
        "editorial_cautions",
        "missing_information",
        mode="before",
    )
    @classmethod
    def normalize_text_list(
        cls,
        value,
    ) -> list[str]:

        if not isinstance(
            value,
            list,
        ):
            return []

        normalized_values = []

        seen_values = set()

        for item in value:

            if not isinstance(
                item,
                str,
            ):
                continue

            cleaned_item = (
                item.strip()
            )

            if not cleaned_item:
                continue

            key = (
                cleaned_item.casefold()
            )

            if key in seen_values:
                continue

            seen_values.add(
                key
            )

            normalized_values.append(
                cleaned_item
            )

        return normalized_values


# ============================================================
# GUIDED RESEARCH REQUEST
# ============================================================

class TouchGuidedResearchRequest(BaseModel):

    action: TouchGuidedResearchAction = (
        "ANSWER"
    )

    message: str = ""

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

    conversation_history: list[
        TouchConversationMessage
    ] = Field(
        default_factory=list,
    )

    current_plan: (
        TouchGuidedResearchPlan
        | None
    ) = None

    @field_validator(
        "message",
        mode="before",
    )
    @classmethod
    def normalize_message(
        cls,
        value,
    ) -> str:

        if not isinstance(
            value,
            str,
        ):
            return ""

        return value.strip()

    @field_validator(
        "output_language",
        mode="before",
    )
    @classmethod
    def normalize_language(
        cls,
        value,
    ) -> str:

        if not isinstance(
            value,
            str,
        ):
            return "fr"

        normalized_value = (
            value
            .strip()
            .lower()
        )

        if normalized_value.startswith(
            "en"
        ):
            return "en"

        return "fr"


# ============================================================
# GUIDED RESEARCH OUTCOME
# ============================================================

class TouchGuidedResearchOutcome(BaseModel):

    phase: TouchGuidedResearchPhase

    assistant_message: str

    questions: list[str] = Field(
        default_factory=list,
    )

    plan: (
        TouchGuidedResearchPlan
        | None
    ) = None

    missing_information: list[str] = Field(
        default_factory=list,
    )

    ready_for_search: bool = False

    used_fallback: bool = False

    error: str | None = None

    @field_validator(
        "assistant_message",
        mode="before",
    )
    @classmethod
    def normalize_assistant_message(
        cls,
        value,
    ) -> str:

        if not isinstance(
            value,
            str,
        ):
            return ""

        return value.strip()

    @field_validator(
        "questions",
        "missing_information",
        mode="before",
    )
    @classmethod
    def normalize_text_list(
        cls,
        value,
    ) -> list[str]:

        if not isinstance(
            value,
            list,
        ):
            return []

        normalized_values = []

        seen_values = set()

        for item in value:

            if not isinstance(
                item,
                str,
            ):
                continue

            cleaned_item = (
                item.strip()
            )

            if not cleaned_item:
                continue

            key = (
                cleaned_item.casefold()
            )

            if key in seen_values:
                continue

            seen_values.add(
                key
            )

            normalized_values.append(
                cleaned_item
            )

        return normalized_values


# ============================================================
# API RESPONSE
# ============================================================

class TouchGuidedResearchResponse(BaseModel):

    status: str

    guided_research: (
        TouchGuidedResearchOutcome
    )
