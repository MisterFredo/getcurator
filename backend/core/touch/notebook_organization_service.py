from typing import (
    Any,
    Optional,
)

from pydantic import (
    BaseModel,
    Field,
)

from core.touch.notebook_models import (
    TouchCorpusNotebook,
    TouchEvidenceNote,
    TouchNotebookContradiction,
    TouchNotebookEvent,
    TouchNotebookNumber,
    TouchNotebookRequest,
    TouchNotebookSection,
    TouchNotebookTimelineItem,
)

from core.touch.notebook_organization_prompt import (
    TOUCH_NOTEBOOK_ORGANIZATION_SYSTEM_PROMPT,
    build_touch_notebook_organization_prompt,
)

from core.touch.notebook_utils import (
    build_retry_prompt,
    extract_json_object,
    unique_ids,
)

from utils.llm import (
    run_llm_json,
)


# ============================================================
# ORGANIZATION RESULT
# ============================================================

class TouchNotebookOrganizationResult(
    BaseModel,
):

    corpus_summary: str = ""

    sections: list[
        TouchNotebookSection
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

    class Config:

        extra = "forbid"


# ============================================================
# NORMALIZE STRING LIST
# ============================================================

def _normalize_string_list(
    value: Any,
) -> list[str]:

    if value is None:
        return []

    if isinstance(
        value,
        str,
    ):

        normalized_value = (
            value.strip()
        )

        return (
            [normalized_value]
            if normalized_value
            else []
        )

    if not isinstance(
        value,
        list,
    ):

        return []

    return unique_ids([

        str(item).strip()

        for item in value

        if (
            item is not None
            and str(item).strip()
        )

    ])


# ============================================================
# NORMALIZE OPTIONAL STRING
# ============================================================

def _normalize_optional_string(
    value: Any,
) -> str | None:

    if value is None:
        return None

    normalized_value = str(
        value
    ).strip()

    return (
        normalized_value
        if normalized_value
        else None
    )


# ============================================================
# NORMALIZE SECTION
# ============================================================

def _normalize_section(
    raw_section: Any,
    index: int,
) -> dict:

    if not isinstance(
        raw_section,
        dict,
    ):

        raise ValueError(
            "Une section du plan n’est pas "
            "un objet JSON"
        )

    return {
        "section_id":
            str(
                raw_section.get(
                    "section_id"
                )
                or f"section-{index + 1:03d}"
            ).strip(),

        "title":
            str(
                raw_section.get(
                    "title"
                )
                or ""
            ).strip(),

        "description":
            str(
                raw_section.get(
                    "description"
                )
                or ""
            ).strip(),

        "event_ids":
            _normalize_string_list(
                raw_section.get(
                    "event_ids"
                )
            ),

        "note_ids":
            _normalize_string_list(
                raw_section.get(
                    "note_ids"
                )
            ),

        "number_ids":
            _normalize_string_list(
                raw_section.get(
                    "number_ids"
                )
            ),
    }


# ============================================================
# NORMALIZE EVENT
# ============================================================

def _normalize_event(
    raw_event: Any,
    index: int,
) -> dict:

    if not isinstance(
        raw_event,
        dict,
    ):

        raise ValueError(
            "Un événement du plan n’est pas "
            "un objet JSON"
        )

    return {
        "event_id":
            str(
                raw_event.get(
                    "event_id"
                )
                or f"event-{index + 1:03d}"
            ).strip(),

        "title":
            str(
                raw_event.get(
                    "title"
                )
                or ""
            ).strip(),

        "description":
            str(
                raw_event.get(
                    "description"
                )
                or ""
            ).strip(),

        "event_date":
            _normalize_optional_string(
                raw_event.get(
                    "event_date"
                )
            ),

        "actors":
            _normalize_string_list(
                raw_event.get(
                    "actors"
                )
            ),

        "note_ids":
            _normalize_string_list(
                raw_event.get(
                    "note_ids"
                )
            ),

        "number_ids":
            _normalize_string_list(
                raw_event.get(
                    "number_ids"
                )
            ),

        "source_content_ids":
            _normalize_string_list(
                raw_event.get(
                    "source_content_ids"
                )
            ),
    }


# ============================================================
# NORMALIZE TIMELINE ITEM
# ============================================================

def _normalize_timeline_item(
    raw_item: Any,
) -> dict:

    if not isinstance(
        raw_item,
        dict,
    ):

        raise ValueError(
            "Un élément de timeline n’est pas "
            "un objet JSON"
        )

    return {
        "date":
            str(
                raw_item.get(
                    "date"
                )
                or ""
            ).strip(),

        "label":
            str(
                raw_item.get(
                    "label"
                )
                or ""
            ).strip(),

        "description":
            str(
                raw_item.get(
                    "description"
                )
                or ""
            ).strip(),

        "event_id":
            _normalize_optional_string(
                raw_item.get(
                    "event_id"
                )
            ),

        "note_ids":
            _normalize_string_list(
                raw_item.get(
                    "note_ids"
                )
            ),

        "source_content_ids":
            _normalize_string_list(
                raw_item.get(
                    "source_content_ids"
                )
            ),
    }


# ============================================================
# NORMALIZE CONTRADICTION
# ============================================================

def _normalize_contradiction(
    raw_contradiction: Any,
) -> dict:

    if not isinstance(
        raw_contradiction,
        dict,
    ):

        raise ValueError(
            "Une contradiction n’est pas "
            "un objet JSON"
        )

    return {
        "subject":
            str(
                raw_contradiction.get(
                    "subject"
                )
                or ""
            ).strip(),

        "description":
            str(
                raw_contradiction.get(
                    "description"
                )
                or ""
            ).strip(),

        "note_ids":
            _normalize_string_list(
                raw_contradiction.get(
                    "note_ids"
                )
            ),

        "source_content_ids":
            _normalize_string_list(
                raw_contradiction.get(
                    "source_content_ids"
                )
            ),

        "resolution":
            _normalize_optional_string(
                raw_contradiction.get(
                    "resolution"
                )
            ),
    }


# ============================================================
# NORMALIZE PAYLOAD
# ============================================================

def _normalize_organization_payload(
    parsed: dict,
) -> dict:

    raw_sections = (
        parsed.get(
            "sections",
            [],
        )
        or []
    )

    raw_events = (
        parsed.get(
            "events",
            [],
        )
        or []
    )

    raw_timeline = (
        parsed.get(
            "timeline",
            [],
        )
        or []
    )

    raw_contradictions = (
        parsed.get(
            "contradictions",
            [],
        )
        or []
    )

    if not isinstance(
        raw_sections,
        list,
    ):

        raw_sections = []

    if not isinstance(
        raw_events,
        list,
    ):

        raw_events = []

    if not isinstance(
        raw_timeline,
        list,
    ):

        raw_timeline = []

    if not isinstance(
        raw_contradictions,
        list,
    ):

        raw_contradictions = []

    return {
        "corpus_summary":
            str(
                parsed.get(
                    "corpus_summary"
                )
                or ""
            ).strip(),

        "sections": [

            _normalize_section(
                raw_section=raw_section,
                index=index,
            )

            for index, raw_section in enumerate(
                raw_sections
            )

        ],

        "events": [

            _normalize_event(
                raw_event=raw_event,
                index=index,
            )

            for index, raw_event in enumerate(
                raw_events
            )

        ],

        "timeline": [

            _normalize_timeline_item(
                raw_item
            )

            for raw_item in raw_timeline

        ],

        "contradictions": [

            _normalize_contradiction(
                raw_contradiction
            )

            for raw_contradiction
            in raw_contradictions

        ],

        "corpus_strengths":
            _normalize_string_list(
                parsed.get(
                    "corpus_strengths"
                )
            ),

        "corpus_limits":
            _normalize_string_list(
                parsed.get(
                    "corpus_limits"
                )
            ),
    }


# ============================================================
# BUILD NOTEBOOK
# ============================================================

def _build_notebook(
    request: TouchNotebookRequest,
    organization:
        TouchNotebookOrganizationResult,
    notes: list[
        TouchEvidenceNote
    ],
    certified_numbers: list[
        TouchNotebookNumber
    ],
) -> TouchCorpusNotebook:

    return TouchCorpusNotebook(

        subject=(
            request.subject.strip()
        ),

        objective=(
            request.objective.strip()
        ),

        corpus_summary=(
            organization
            .corpus_summary
            .strip()
        ),

        sections=(
            organization.sections
        ),

        notes=notes,

        events=(
            organization.events
        ),

        timeline=(
            organization.timeline
        ),

        dimensions=[],

        validated_numbers=(
            certified_numbers
        ),

        quarantined_numbers=[],

        contradictions=(
            organization.contradictions
        ),

        corpus_strengths=(
            organization.corpus_strengths
        ),

        corpus_limits=(
            organization.corpus_limits
        ),

    )


# ============================================================
# ORGANIZE NOTEBOOK
# ============================================================

def organize_notebook(
    request: TouchNotebookRequest,
    notes: list[
        TouchEvidenceNote
    ],
    certified_numbers: list[
        TouchNotebookNumber
    ],
    model: Optional[str] = None,
    max_attempts: int = 2,
) -> TouchCorpusNotebook:

    if not notes and not certified_numbers:

        raise ValueError(
            "Aucune pièce documentaire "
            "à organiser"
        )

    original_prompt = (
        build_touch_notebook_organization_prompt(

            request=request,

            notes=notes,

            certified_numbers=(
                certified_numbers
            ),

        )
    )

    prompt = original_prompt

    attempts = max(
        1,
        max_attempts,
    )

    last_error = (
        "Erreur inconnue pendant "
        "l’organisation du notebook"
    )

    for attempt in range(
        attempts
    ):

        try:

            raw_content = run_llm_json(

                prompt=prompt,

                model=model,

                temperature=0.0,

                system_prompt=(
                    TOUCH_NOTEBOOK_ORGANIZATION_SYSTEM_PROMPT
                ),

            )

            parsed = extract_json_object(
                raw_content
            )

            normalized_payload = (
                _normalize_organization_payload(
                    parsed
                )
            )

            organization = (
                TouchNotebookOrganizationResult
                .model_validate(
                    normalized_payload
                )
            )

            return _build_notebook(

                request=request,

                organization=(
                    organization
                ),

                notes=notes,

                certified_numbers=(
                    certified_numbers
                ),

            )

        except Exception as exc:

            last_error = str(
                exc
            )

            if (
                attempt + 1
                >= attempts
            ):

                break

            prompt = build_retry_prompt(

                original_prompt=(
                    original_prompt
                ),

                error=last_error,

            )

    raise ValueError(
        "Échec de l’organisation du notebook "
        f"après {attempts} tentative(s) : "
        f"{last_error}"
    )
