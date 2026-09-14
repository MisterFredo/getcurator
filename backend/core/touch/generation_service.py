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

# ============================================================
# VALIDATE DRAFT
# ============================================================

def _validate_draft(
    draft: TouchOnePagerDraft,
    allowed_content_ids: set[str],
) -> None:

    if not draft.title:

        raise ValueError(
            "Le draft Touch ne possède "
            "pas de titre"
        )

    if not draft.subtitle:

        raise ValueError(
            "Le draft Touch ne possède "
            "pas de sous-titre"
        )

    if not draft.executive_takeaways:

        raise ValueError(
            "Le draft Touch ne possède "
            "aucun executive takeaway"
        )

    section_types = [

        section.section_type

        for section in draft.sections

    ]

    if (
        section_types.count(
            "WHAT_HAPPENED"
        )
        != 1
    ):

        raise ValueError(
            "Le draft Touch doit contenir "
            "exactement une section "
            "WHAT_HAPPENED"
        )

    if (
        section_types.count(
            "WHY_IT_MATTERS"
        )
        != 1
    ):

        raise ValueError(
            "Le draft Touch doit contenir "
            "exactement une section "
            "WHY_IT_MATTERS"
        )

    if (
        len(section_types)
        != len(set(section_types))
    ):

        raise ValueError(
            "Le draft Touch contient plusieurs "
            "sections du même type"
        )

    source_groups = []

    for takeaway in draft.executive_takeaways:

        source_groups.append(
            takeaway.source_content_ids
        )

    for section in draft.sections:

        source_groups.append(
            section.source_content_ids
        )

    for number in draft.key_numbers:

        source_groups.append(
            number.source_content_ids
        )

    for watch_point in draft.what_to_watch:

        source_groups.append(
            watch_point.source_content_ids
        )

    for source_content_ids in source_groups:

        if not source_content_ids:

            raise ValueError(
                "Un bloc du draft Touch "
                "ne possède aucune source"
            )

        unknown_ids = (

            set(source_content_ids)

            - allowed_content_ids

        )

        if unknown_ids:

            raise ValueError(
                "Le draft Touch cite des "
                "content_id inconnus : "
                + ", ".join(
                    sorted(unknown_ids)
                )
            )


# ============================================================
# BUILD RETRY PROMPT
# ============================================================

def _build_generation_retry_prompt(
    original_prompt: str,
    error: str,
) -> str:

    return f"""
{original_prompt}


============================================================
CORRECTION REQUIRED
============================================================

The previous response was invalid.

Validation error:

{error}

Return exactly one valid JSON object.

Use only supplied content_id values.

Every generated block must contain at least one valid source.

Return WHAT_HAPPENED exactly once.

Return WHY_IT_MATTERS exactly once.

Do not return duplicate section types.

Do not include Markdown fences.

Do not include text outside the JSON object.
""".strip()


# ============================================================
# GENERATE DRAFT
# ============================================================

def _generate_draft(
    request: TouchGenerationRequest,
    contents: list,
    model: Optional[str],
    max_attempts: int,
) -> TouchOnePagerDraft:

    original_prompt = (
        build_touch_generation_prompt(

            request=request,

            contents=contents,

        )
    )

    prompt = original_prompt

    allowed_content_ids = {

        content.id

        for content in contents

    }

    last_error = (
        "Erreur inconnue du moteur "
        "de génération Touch"
    )

    for attempt in range(
        max(1, max_attempts)
    ):

        try:

            raw_content = run_llm_json(

                prompt=prompt,

                model=model,

                temperature=0.0,

                system_prompt=(
                    TOUCH_GENERATION_SYSTEM_PROMPT
                ),

            )

            parsed = _extract_json_object(
                raw_content
            )

            draft = (
                TouchOnePagerDraft
                .model_validate(
                    parsed
                )
            )

            draft = _normalize_draft(
                draft
            )

            _validate_draft(

                draft=draft,

                allowed_content_ids=(
                    allowed_content_ids
                ),

            )

            return draft

        except Exception as exc:

            last_error = str(exc)

            if (
                attempt + 1
                >= max(1, max_attempts)
            ):

                break

            prompt = (
                _build_generation_retry_prompt(

                    original_prompt=(
                        original_prompt
                    ),

                    error=last_error,

                )
            )

    raise ValueError(
        "Échec de la génération Touch "
        f"après {max_attempts} tentative(s) : "
        f"{last_error}"
    )


# ============================================================
# BUILD DOCUMENT SOURCES
# ============================================================

def _build_document_sources(
    contents: list,
) -> list[
    TouchDocumentSource
]:

    sources = []

    for content in contents:

        published_at = None

        if content.published_at:

            published_at = (
                content
                .published_at
                .isoformat()
            )

        sources.append(

            TouchDocumentSource(

                content_id=
                    content.id,

                title=
                    content.title,

                source_title=(
                    content.source_title
                    or ""
                ),

                source_url=(
                    content.source_url
                    or ""
                ),

                published_at=
                    published_at,

            )

        )

    return sources

# ============================================================
# GENERATE TOUCH ONE-PAGER
# ============================================================

def generate_touch_one_pager(
    request: TouchGenerationRequest,
    model: Optional[str] = None,
) -> TouchGenerationOutcome:

    try:

        content_ids = _unique_ids(
            request.content_ids
        )

        if not content_ids:

            raise ValueError(
                "Le corpus Touch est vide"
            )

        language = _normalize_language(
            request.output_language
        )

        contents = load_contents_by_ids(

            content_ids=content_ids,

            language=language,

        )

        loaded_content_ids = {

            content.id

            for content in contents

        }

        missing_content_ids = (

            set(
                content_ids
            )

            - loaded_content_ids

        )

        if missing_content_ids:

            raise ValueError(
                "Certains contenus Touch sont "
                "introuvables : "
                + ", ".join(
                    sorted(
                        missing_content_ids
                    )
                )
            )

        draft = _generate_draft(

            request=request,

            contents=contents,

            model=model,

            max_attempts=(
                DEFAULT_TOUCH_GENERATION_ATTEMPTS
            ),

        )

        sources = _build_document_sources(
            contents=contents,
        )

        return TouchGenerationOutcome(

            status="GENERATED",

            draft=draft,

            sources=sources,

            error=None,

        )

    except Exception as exc:

        return TouchGenerationOutcome(

            status="GENERATION_FAILED",

            draft=None,

            sources=[],

            error=str(
                exc
            )[:2000],

        )
