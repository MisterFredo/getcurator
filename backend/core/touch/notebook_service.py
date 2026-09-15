import json

from typing import (
    Any,
    Optional,
)

from pydantic import (
    BaseModel,
    Field,
)

from core.expertise.content_service import (
    load_contents_by_ids,
)

from core.touch.notebook_models import (
    TouchCorpusNotebook,
    TouchNotebookOutcome,
    TouchNotebookRequest,
)

from core.touch.notebook_prompt import (
    TOUCH_NOTEBOOK_CONSOLIDATION_SYSTEM_PROMPT,
    TOUCH_NOTEBOOK_EXTRACTION_SYSTEM_PROMPT,
    build_touch_notebook_consolidation_prompt,
    build_touch_notebook_extraction_prompt,
)

from utils.llm import (
    run_llm_json,
)


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_TOUCH_NOTEBOOK_BATCH_SIZE = 5

DEFAULT_TOUCH_NOTEBOOK_ATTEMPTS = 2


# ============================================================
# INTERNAL MODELS
# ============================================================

class StrictTouchExtractionModel(
    BaseModel,
):

    class Config:

        extra = "forbid"


class TouchExtractedNote(
    StrictTouchExtractionModel,
):

    temporary_note_id: str

    note_type: str

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

    confidence: str

    status: str

    source_content_id: str


class TouchExtractedNumber(
    StrictTouchExtractionModel,
):

    temporary_number_id: str

    value: str

    unit: str = ""

    metric: str = ""

    context: str = ""

    actor: str | None = None

    geography: str | None = None

    period: str | None = None

    confidence: str

    source_content_id: str

    ambiguity: str = ""


class TouchExtractionResult(
    StrictTouchExtractionModel,
):

    notes: list[
        TouchExtractedNote
    ] = Field(
        default_factory=list,
    )

    numbers: list[
        TouchExtractedNumber
    ] = Field(
        default_factory=list,
    )


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
            "de notebook Touch"
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
                "la réponse du notebook Touch"
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
                "le moteur de notebook Touch"
            ) from exc

    if not isinstance(
        parsed,
        dict,
    ):

        raise ValueError(
            "La réponse du notebook Touch "
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
        language.strip().lower()
        if isinstance(
            language,
            str,
        )
        else ""
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

    result = []

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

        result.append(
            cleaned_value
        )

    return result


# ============================================================
# BUILD BATCHES
# ============================================================

def _build_batches(
    values: list[Any],
    batch_size: int,
) -> list[list[Any]]:

    safe_batch_size = max(
        1,
        batch_size,
    )

    return [

        values[
            start:
            start + safe_batch_size
        ]

        for start in range(
            0,
            len(
                values
            ),
            safe_batch_size,
        )

    ]


# ============================================================
# RETRY PROMPT
# ============================================================

def _build_retry_prompt(
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

Correct the response while respecting the required JSON
structure.

Use only supplied source_content_ids.

Do not invent identifiers.

Return only the corrected JSON object.
""".strip()


# ============================================================
# VALIDATE EXTRACTION SOURCES
# ============================================================

def _validate_extraction_sources(
    extraction: TouchExtractionResult,
    allowed_content_ids: set[str],
) -> None:

    returned_source_ids = {

        note.source_content_id

        for note in extraction.notes

    }

    returned_source_ids.update({

        number.source_content_id

        for number in extraction.numbers

    })

    unknown_source_ids = (

        returned_source_ids
        - allowed_content_ids

    )

    if unknown_source_ids:

        raise ValueError(
            "Le moteur d’extraction a inventé "
            "des source_content_ids : "
            + ", ".join(
                sorted(
                    unknown_source_ids
                )
            )
        )


# ============================================================
# EXTRACT ONE BATCH
# ============================================================

def _extract_batch(
    request: TouchNotebookRequest,
    contents: list[Any],
    model: Optional[str],
    max_attempts: int,
) -> TouchExtractionResult:

    original_prompt = (
        build_touch_notebook_extraction_prompt(

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
        "Erreur inconnue pendant "
        "l’extraction du notebook"
    )

    for attempt in range(
        max(
            1,
            max_attempts,
        )
    ):

        try:

            raw_content = run_llm_json(

                prompt=prompt,

                model=model,

                temperature=0.0,

                system_prompt=(
                    TOUCH_NOTEBOOK_EXTRACTION_SYSTEM_PROMPT
                ),

            )

            parsed = _extract_json_object(
                raw_content
            )

            extraction = (
                TouchExtractionResult
                .model_validate(
                    parsed
                )
            )

            _validate_extraction_sources(

                extraction=extraction,

                allowed_content_ids=(
                    allowed_content_ids
                ),

            )

            return extraction

        except Exception as exc:

            last_error = str(
                exc
            )

            if (
                attempt + 1
                >= max_attempts
            ):

                break

            prompt = _build_retry_prompt(

                original_prompt=(
                    original_prompt
                ),

                error=last_error,

            )

    raise ValueError(
        "Échec de l’extraction d’un lot "
        f"après {max_attempts} tentative(s) : "
        f"{last_error}"
    )


# ============================================================
# PREFIX TEMPORARY IDS
# ============================================================

def _prefix_extraction_ids(
    extraction: TouchExtractionResult,
    batch_index: int,
) -> dict:

    payload = extraction.model_dump(
        mode="json",
    )

    for note_index, note in enumerate(
        payload.get(
            "notes",
            [],
        ),
        start=1,
    ):

        note["temporary_note_id"] = (
            f"batch-{batch_index:03d}"
            f"-note-{note_index:03d}"
        )

    for number_index, number in enumerate(
        payload.get(
            "numbers",
            [],
        ),
        start=1,
    ):

        number["temporary_number_id"] = (
            f"batch-{batch_index:03d}"
            f"-number-{number_index:03d}"
        )

    return payload


# ============================================================
# NORMALIZE NOTEBOOK
# ============================================================

def _normalize_notebook(
    notebook: TouchCorpusNotebook,
) -> TouchCorpusNotebook:

    notes = [

        note.model_copy(
            update={

                "note_id":
                    note.note_id.strip(),

                "statement":
                    note.statement.strip(),

                "explanation":
                    note.explanation.strip(),

                "actors":
                    _unique_ids(
                        note.actors
                    ),

                "geographies":
                    _unique_ids(
                        note.geographies
                    ),

                "dates":
                    _unique_ids(
                        note.dates
                    ),

                "source_content_ids":
                    _unique_ids(
                        note.source_content_ids
                    ),

            },
        )

        for note in notebook.notes

    ]

    events = [

        event.model_copy(
            update={

                "event_id":
                    event.event_id.strip(),

                "title":
                    event.title.strip(),

                "description":
                    event.description.strip(),

                "event_date":
                    (
                        event.event_date.strip()
                        if event.event_date
                        else None
                    ),

                "actors":
                    _unique_ids(
                        event.actors
                    ),

                "note_ids":
                    _unique_ids(
                        event.note_ids
                    ),

                "source_content_ids":
                    _unique_ids(
                        event.source_content_ids
                    ),

            },
        )

        for event in notebook.events

    ]

    timeline = [

        item.model_copy(
            update={

                "date":
                    item.date.strip(),

                "label":
                    item.label.strip(),

                "description":
                    item.description.strip(),

                "event_id":
                    (
                        item.event_id.strip()
                        if item.event_id
                        else None
                    ),

                "note_ids":
                    _unique_ids(
                        item.note_ids
                    ),

                "source_content_ids":
                    _unique_ids(
                        item.source_content_ids
                    ),

            },
        )

        for item in notebook.timeline

    ]

    dimensions = [

        dimension.model_copy(
            update={

                "label":
                    dimension.label.strip(),

                "summary":
                    dimension.summary.strip(),

                "note_ids":
                    _unique_ids(
                        dimension.note_ids
                    ),

                "source_content_ids":
                    _unique_ids(
                        dimension.source_content_ids
                    ),

            },
        )

        for dimension in notebook.dimensions

    ]

    validated_numbers = [

        number.model_copy(
            update={

                "number_id":
                    number.number_id.strip(),

                "value":
                    number.value.strip(),

                "unit":
                    number.unit.strip(),

                "metric":
                    number.metric.strip(),

                "context":
                    number.context.strip(),

                "actor":
                    (
                        number.actor.strip()
                        if number.actor
                        else None
                    ),

                "geography":
                    (
                        number.geography.strip()
                        if number.geography
                        else None
                    ),

                "period":
                    (
                        number.period.strip()
                        if number.period
                        else None
                    ),

                "note_ids":
                    _unique_ids(
                        number.note_ids
                    ),

                "source_content_ids":
                    _unique_ids(
                        number.source_content_ids
                    ),

            },
        )

        for number in notebook.validated_numbers

    ]

    quarantined_numbers = [

        number.model_copy(
            update={

                "value":
                    number.value.strip(),

                "unit":
                    number.unit.strip(),

                "metric":
                    number.metric.strip(),

                "context":
                    number.context.strip(),

                "reason":
                    number.reason.strip(),

                "source_content_ids":
                    _unique_ids(
                        number.source_content_ids
                    ),

            },
        )

        for number in notebook.quarantined_numbers

    ]

    contradictions = [

        contradiction.model_copy(
            update={

                "subject":
                    contradiction.subject.strip(),

                "description":
                    contradiction.description.strip(),

                "note_ids":
                    _unique_ids(
                        contradiction.note_ids
                    ),

                "source_content_ids":
                    _unique_ids(
                        contradiction.source_content_ids
                    ),

                "resolution":
                    (
                        contradiction.resolution.strip()
                        if contradiction.resolution
                        else None
                    ),

            },
        )

        for contradiction in notebook.contradictions

    ]

    return notebook.model_copy(
        update={

            "subject":
                notebook.subject.strip(),

            "objective":
                notebook.objective.strip(),

            "corpus_summary":
                notebook.corpus_summary.strip(),

            "notes":
                notes,

            "events":
                events,

            "timeline":
                timeline,

            "dimensions":
                dimensions,

            "validated_numbers":
                validated_numbers,

            "quarantined_numbers":
                quarantined_numbers,

            "contradictions":
                contradictions,

            "corpus_strengths":
                _unique_ids(
                    notebook.corpus_strengths
                ),

            "corpus_limits":
                _unique_ids(
                    notebook.corpus_limits
                ),

        },
    )


# ============================================================
# VALIDATE UNIQUE IDENTIFIERS
# ============================================================

def _validate_unique_identifiers(
    values: list[str],
    label: str,
) -> None:

    if len(
        values
    ) != len(
        set(
            values
        )
    ):

        raise ValueError(
            f"Le notebook contient des {label} "
            "dupliqués"
        )

    if any(
        not value
        for value in values
    ):

        raise ValueError(
            f"Le notebook contient un {label} vide"
        )


# ============================================================
# VALIDATE REFERENCES
# ============================================================

def _validate_notebook_references(
    notebook: TouchCorpusNotebook,
    allowed_content_ids: set[str],
) -> None:

    note_ids = [

        note.note_id

        for note in notebook.notes

    ]

    event_ids = [

        event.event_id

        for event in notebook.events

    ]

    number_ids = [

        number.number_id

        for number in notebook.validated_numbers

    ]

    _validate_unique_identifiers(
        values=note_ids,
        label="note_id",
    )

    _validate_unique_identifiers(
        values=event_ids,
        label="event_id",
    )

    _validate_unique_identifiers(
        values=number_ids,
        label="number_id",
    )

    note_id_set = set(
        note_ids
    )

    event_id_set = set(
        event_ids
    )

    referenced_note_ids = set()

    referenced_event_ids = set()

    referenced_source_ids = set()

    for note in notebook.notes:

        referenced_source_ids.update(
            note.source_content_ids
        )

        if not note.source_content_ids:

            raise ValueError(
                "Une note consolidée ne possède "
                "aucune source"
            )

    for event in notebook.events:

        referenced_note_ids.update(
            event.note_ids
        )

        referenced_source_ids.update(
            event.source_content_ids
        )

    for item in notebook.timeline:

        referenced_note_ids.update(
            item.note_ids
        )

        referenced_source_ids.update(
            item.source_content_ids
        )

        if item.event_id:

            referenced_event_ids.add(
                item.event_id
            )

    for dimension in notebook.dimensions:

        referenced_note_ids.update(
            dimension.note_ids
        )

        referenced_source_ids.update(
            dimension.source_content_ids
        )

    for number in notebook.validated_numbers:

        referenced_note_ids.update(
            number.note_ids
        )

        referenced_source_ids.update(
            number.source_content_ids
        )

        if not number.source_content_ids:

            raise ValueError(
                "Un chiffre validé ne possède "
                "aucune source"
            )

    for number in notebook.quarantined_numbers:

        referenced_source_ids.update(
            number.source_content_ids
        )

    for contradiction in notebook.contradictions:

        referenced_note_ids.update(
            contradiction.note_ids
        )

        referenced_source_ids.update(
            contradiction.source_content_ids
        )

    unknown_note_ids = (

        referenced_note_ids
        - note_id_set

    )

    if unknown_note_ids:

        raise ValueError(
            "Le notebook référence des note_ids "
            "inconnus : "
            + ", ".join(
                sorted(
                    unknown_note_ids
                )
            )
        )

    unknown_event_ids = (

        referenced_event_ids
        - event_id_set

    )

    if unknown_event_ids:

        raise ValueError(
            "La timeline référence des event_ids "
            "inconnus : "
            + ", ".join(
                sorted(
                    unknown_event_ids
                )
            )
        )

    unknown_source_ids = (

        referenced_source_ids
        - allowed_content_ids

    )

    if unknown_source_ids:

        raise ValueError(
            "Le notebook référence des sources "
            "inconnues : "
            + ", ".join(
                sorted(
                    unknown_source_ids
                )
            )
        )


# ============================================================
# CONSOLIDATE NOTEBOOK
# ============================================================

def _consolidate_notebook(
    request: TouchNotebookRequest,
    extracted_batches: list[dict],
    model: Optional[str],
    max_attempts: int,
) -> TouchCorpusNotebook:

    original_prompt = (
        build_touch_notebook_consolidation_prompt(

            request=request,

            extracted_batches=(
                extracted_batches
            ),

        )
    )

    prompt = original_prompt

    allowed_content_ids = set(
        request.content_ids
    )

    last_error = (
        "Erreur inconnue pendant la "
        "consolidation du notebook"
    )

    for attempt in range(
        max(
            1,
            max_attempts,
        )
    ):

        try:

            raw_content = run_llm_json(

                prompt=prompt,

                model=model,

                temperature=0.0,

                system_prompt=(
                    TOUCH_NOTEBOOK_CONSOLIDATION_SYSTEM_PROMPT
                ),

            )

            parsed = _extract_json_object(
                raw_content
            )

            notebook = (
                TouchCorpusNotebook
                .model_validate(
                    parsed
                )
            )

            notebook = _normalize_notebook(
                notebook
            )

            _validate_notebook_references(

                notebook=notebook,

                allowed_content_ids=(
                    allowed_content_ids
                ),

            )

            return notebook

        except Exception as exc:

            last_error = str(
                exc
            )

            if (
                attempt + 1
                >= max_attempts
            ):

                break

            prompt = _build_retry_prompt(

                original_prompt=(
                    original_prompt
                ),

                error=last_error,

            )

    raise ValueError(
        "Échec de la consolidation du notebook "
        f"après {max_attempts} tentative(s) : "
        f"{last_error}"
    )


# ============================================================
# BUILD TOUCH NOTEBOOK
# ============================================================

def build_touch_notebook(
    request: TouchNotebookRequest,
    model: Optional[str] = None,
) -> TouchNotebookOutcome:

    try:

        content_ids = _unique_ids(
            request.content_ids
        )

        if not content_ids:

            raise ValueError(
                "Le corpus Touch est vide"
            )

        subject = request.subject.strip()

        if not subject:

            raise ValueError(
                "Le sujet du notebook Touch "
                "est obligatoire"
            )

        language = _normalize_language(
            request.output_language
        )

        normalized_request = (
            request.model_copy(
                update={

                    "subject":
                        subject,

                    "objective":
                        request.objective.strip(),

                    "content_ids":
                        content_ids,

                    "output_language":
                        language,

                },
            )
        )

        contents = load_contents_by_ids(

            content_ids=content_ids,

            language=language,

        )

        loaded_contents_by_id = {

            content.id:
                content

            for content in contents

        }

        missing_content_ids = [

            content_id

            for content_id in content_ids

            if (
                content_id
                not in loaded_contents_by_id
            )

        ]

        if missing_content_ids:

            raise ValueError(
                "Certains contenus Touch sont "
                "introuvables : "
                + ", ".join(
                    missing_content_ids
                )
            )

        ordered_contents = [

            loaded_contents_by_id[
                content_id
            ]

            for content_id in content_ids

        ]

        content_batches = _build_batches(

            values=ordered_contents,

            batch_size=(
                DEFAULT_TOUCH_NOTEBOOK_BATCH_SIZE
            ),

        )

        extracted_batches = []

        for batch_index, content_batch in enumerate(
            content_batches,
            start=1,
        ):

            extraction = _extract_batch(

                request=normalized_request,

                contents=content_batch,

                model=model,

                max_attempts=(
                    DEFAULT_TOUCH_NOTEBOOK_ATTEMPTS
                ),

            )

            extracted_batches.append(

                _prefix_extraction_ids(

                    extraction=extraction,

                    batch_index=batch_index,

                )

            )

        notebook = _consolidate_notebook(

            request=normalized_request,

            extracted_batches=(
                extracted_batches
            ),

            model=model,

            max_attempts=(
                DEFAULT_TOUCH_NOTEBOOK_ATTEMPTS
            ),

        )

        return TouchNotebookOutcome(

            status="GENERATED",

            notebook=notebook,

            source_count=len(
                ordered_contents
            ),

            error=None,

        )

    except Exception as exc:

        return TouchNotebookOutcome(

            status="GENERATION_FAILED",

            notebook=None,

            source_count=0,

            error=str(
                exc
            )[:2000],

        )
