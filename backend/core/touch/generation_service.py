import json

from typing import (
    Optional,
)

from core.expertise.content_service import (
    load_contents_by_ids,
)

from core.touch.generation_models import (
    TouchDocumentSource,
    TouchGenerationOutcome,
    TouchGenerationRequest,
    TouchNarrativeSection,
    TouchOnePagerDraft,
)

from core.touch.generation_prompt import (
    TOUCH_GENERATION_SYSTEM_PROMPT,
    build_touch_generation_prompt,
)

from utils.llm import (
    run_llm_json,
)


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_TOUCH_GENERATION_ATTEMPTS = 2


# ============================================================
# EXTRACT JSON
# ============================================================

def _extract_json_object(
    raw_content: str,
) -> dict:

    content = (
        raw_content.strip()
        if isinstance(
            raw_content,
            str,
        )
        else ""
    )

    if not content:

        raise ValueError(
            "Réponse vide du moteur "
            "de génération Touch"
        )

    try:

        parsed = json.loads(
            content
        )

    except json.JSONDecodeError:

        first_brace = content.find(
            "{"
        )

        last_brace = content.rfind(
            "}"
        )

        if (
            first_brace < 0
            or last_brace < first_brace
        ):

            raise ValueError(
                "Aucun objet JSON trouvé dans "
                "la réponse de génération Touch"
            )

        extracted_content = content[
            first_brace:
            last_brace + 1
        ]

        try:

            parsed = json.loads(
                extracted_content
            )

        except json.JSONDecodeError as exc:

            raise ValueError(
                "JSON invalide retourné par "
                "le moteur de génération Touch"
            ) from exc

    if not isinstance(
        parsed,
        dict,
    ):

        raise ValueError(
            "La réponse de génération Touch "
            "n’est pas un objet JSON"
        )

    return parsed


# ============================================================
# NORMALIZE LANGUAGE
# ============================================================

def _normalize_language(
    language: str,
) -> str:

    normalized = (
        language
        .strip()
        .lower()
    )

    if normalized.startswith(
        "en"
    ):

        return "en"

    return "fr"


# ============================================================
# UNIQUE IDS
# ============================================================

def _unique_ids(
    values: list[str],
) -> list[str]:

    unique_values = []

    seen_values = set()

    for value in values:

        if not isinstance(
            value,
            str,
        ):

            continue

        cleaned_value = value.strip()

        if (
            not cleaned_value
            or cleaned_value in seen_values
        ):

            continue

        seen_values.add(
            cleaned_value
        )

        unique_values.append(
            cleaned_value
        )

    return unique_values


# ============================================================
# NORMALIZE SECTION
# ============================================================

def _normalize_section(
    section: TouchNarrativeSection,
) -> TouchNarrativeSection:

    return section.model_copy(

        update={

            "title":
                section.title.strip(),

            "body":
                section.body.strip(),

            "source_content_ids":
                _unique_ids(
                    section.source_content_ids
                ),

        },

    )


# ============================================================
# NORMALIZE DRAFT
# ============================================================

def _normalize_draft(
    draft: TouchOnePagerDraft,
) -> TouchOnePagerDraft:

    executive_takeaways = [

        takeaway.model_copy(
            update={
                "statement":
                    takeaway.statement.strip(),

                "source_content_ids":
                    _unique_ids(
                        takeaway.source_content_ids
                    ),
            },
        )

        for takeaway in draft.executive_takeaways

    ]

    sections = [

        _normalize_section(
            section
        )

        for section in draft.sections

    ]

    key_numbers = [

        number.model_copy(
            update={
                "value":
                    number.value.strip(),

                "label":
                    number.label.strip(),

                "context":
                    number.context.strip(),

                "source_content_ids":
                    _unique_ids(
                        number.source_content_ids
                    ),
            },
        )

        for number in draft.key_numbers

    ]

    what_to_watch = [

        watch_point.model_copy(
            update={
                "label":
                    watch_point.label.strip(),

                "explanation":
                    watch_point.explanation.strip(),

                "source_content_ids":
                    _unique_ids(
                        watch_point.source_content_ids
                    ),
            },
        )

        for watch_point in draft.what_to_watch

    ]

    return draft.model_copy(
        update={
            "title":
                draft.title.strip(),

            "subtitle":
                draft.subtitle.strip(),

            "executive_takeaways":
                executive_takeaways,

            "sections":
                sections,

            "key_numbers":
                key_numbers,

            "what_to_watch":
                what_to_watch,
        },
    )
