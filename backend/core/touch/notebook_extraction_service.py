from typing import (
    Any,
    Optional,
)

from pydantic import (
    BaseModel,
    Field,
)

from api.expertise.models import (
    ExpertiseContent,
)

from core.touch.notebook_models import (
    TouchNotebookRequest,
)

from core.touch.notebook_prompt import (
    TOUCH_NOTEBOOK_EXTRACTION_SYSTEM_PROMPT,
    build_touch_notebook_extraction_prompt,
)

from core.touch.notebook_utils import (
    build_batches,
    build_retry_prompt,
    extract_json_object,
    unique_ids,
)

from utils.llm import (
    run_llm_json,
)


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

    explanation: str | None = None

    actors: list[str] = Field(
        default_factory=list,
    )

    geographies: list[str] = Field(
        default_factory=list,
    )

    dates: list[str] = Field(
        default_factory=list,
    )

    confidence: str = "MEDIUM"

    status: str = "VALIDATED"

    source_content_ids: list[str] = Field(
        default_factory=list,
    )


class TouchExtractionResult(
    StrictTouchExtractionModel,
):

    notes: list[
        TouchExtractedNote
    ] = Field(
        default_factory=list,
    )


# ============================================================
# NORMALIZE STRING LIST
# ============================================================

def _normalize_string_list(
    value: Any,
) -> list[str]:

    if isinstance(
        value,
        str,
    ):

        values = [
            value
        ]

    elif isinstance(
        value,
        list,
    ):

        values = value

    else:

        values = []

    return unique_ids([

        str(item).strip()

        for item in values

        if (
            item is not None
            and str(item).strip()
        )

    ])


# ============================================================
# NORMALIZE RAW NOTE
# ============================================================

def _normalize_raw_note(
    note: dict,
    note_index: int,
) -> dict:

    normalized = dict(
        note
    )

    normalized[
        "temporary_note_id"
    ] = str(
        normalized.get(
            "temporary_note_id"
        )
        or f"note-{note_index:03d}"
    ).strip()

    # ========================================================
    # SINGULAR ALIASES
    # ========================================================

    singular_actor = normalized.pop(
        "actor",
        None,
    )

    singular_geography = normalized.pop(
        "geography",
        None,
    )

    singular_date = normalized.pop(
        "date",
        None,
    )

    # ========================================================
    # ACTORS
    # ========================================================

    actors = _normalize_string_list(
        normalized.get(
            "actors"
        )
    )

    if (
        singular_actor is not None
        and str(
            singular_actor
        ).strip()
    ):

        actors = unique_ids(
            actors
            + [
                str(
                    singular_actor
                ).strip()
            ]
        )

    normalized["actors"] = actors

    # ========================================================
    # GEOGRAPHIES
    # ========================================================

    geographies = _normalize_string_list(
        normalized.get(
            "geographies"
        )
    )

    if (
        singular_geography is not None
        and str(
            singular_geography
        ).strip()
    ):

        geographies = unique_ids(
            geographies
            + [
                str(
                    singular_geography
                ).strip()
            ]
        )

    normalized[
        "geographies"
    ] = geographies

    # ========================================================
    # DATES
    # ========================================================

    dates = _normalize_string_list(
        normalized.get(
            "dates"
        )
    )

    if (
        singular_date is not None
        and str(
            singular_date
        ).strip()
    ):

        dates = unique_ids(
            dates
            + [
                str(
                    singular_date
                ).strip()
            ]
        )

    normalized["dates"] = dates

    # ========================================================
    # TEXT
    # ========================================================

    normalized["statement"] = str(
        normalized.get(
            "statement"
        )
        or ""
    ).strip()

    normalized["explanation"] = str(
        normalized.get(
            "explanation"
        )
        or ""
    ).strip()

    # ========================================================
    # ENUM-LIKE FIELDS
    # ========================================================

    normalized["note_type"] = str(
        normalized.get(
            "note_type"
        )
        or "FACT"
    ).strip().upper()

    normalized["confidence"] = str(
        normalized.get(
            "confidence"
        )
        or "MEDIUM"
    ).strip().upper()

    normalized["status"] = str(
        normalized.get(
            "status"
        )
        or "VALIDATED"
    ).strip().upper()

    # ========================================================
    # SOURCE IDENTIFIERS
    # ========================================================

    singular_source_id = (
        normalized.pop(
            "source_content_id",
            None,
        )
        or normalized.pop(
            "content_id",
            None,
        )
        or normalized.pop(
            "source_id",
            None,
        )
    )

    source_content_ids = (
        _normalize_string_list(
            normalized.get(
                "source_content_ids"
            )
        )
    )

    if (
        singular_source_id is not None
        and str(
            singular_source_id
        ).strip()
    ):

        source_content_ids = unique_ids(
            source_content_ids
            + [
                str(
                    singular_source_id
                ).strip()
            ]
        )

    normalized[
        "source_content_ids"
    ] = source_content_ids

    return normalized


# ============================================================
# NORMALIZE EXTRACTION PAYLOAD
# ============================================================

def _normalize_extraction_payload(
    parsed: dict,
) -> dict:

    raw_notes = (
        parsed.get(
            "notes",
            [],
        )
        or []
    )

    if not isinstance(
        raw_notes,
        list,
    ):

        raise ValueError(
            "Le champ notes retourné par "
            "le moteur n’est pas une liste"
        )

    normalized_notes = []

    for note_index, note in enumerate(
        raw_notes,
        start=1,
    ):

        if not isinstance(
            note,
            dict,
        ):

            raise ValueError(
                "Une note retournée par le "
                "moteur n’est pas un objet"
            )

        normalized_notes.append(

            _normalize_raw_note(
                note=note,
                note_index=note_index,
            )

        )

    return {
        "notes":
            normalized_notes,
    }


# ============================================================
# VALIDATE EXTRACTION SOURCES
# ============================================================

def _validate_extraction_sources(
    extraction: TouchExtractionResult,
    allowed_content_ids: set[str],
) -> None:

    returned_source_ids = {

        source_content_id

        for note in extraction.notes

        for source_content_id
        in note.source_content_ids

    }

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

    notes_without_sources = [

        note.temporary_note_id

        for note in extraction.notes

        if not note.source_content_ids

    ]

    if notes_without_sources:

        raise ValueError(
            "Le moteur d’extraction a retourné "
            "des notes sans source : "
            + ", ".join(
                notes_without_sources
            )
        )


# ============================================================
# EXTRACT ONE BATCH
# ============================================================

def _extract_batch(
    request: TouchNotebookRequest,
    contents: list[
        ExpertiseContent
    ],
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

            parsed = extract_json_object(
                raw_content
            )

            normalized_payload = (
                _normalize_extraction_payload(
                    parsed
                )
            )

            extraction = (
                TouchExtractionResult
                .model_validate(
                    normalized_payload
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

            prompt = build_retry_prompt(

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

    return payload


# ============================================================
# EXTRACT NOTEBOOK BATCHES
# ============================================================

def extract_notebook_batches(
    request: TouchNotebookRequest,
    contents: list[
        ExpertiseContent
    ],
    batch_size: int,
    max_attempts: int,
    model: Optional[str] = None,
) -> list[dict]:

    content_batches = build_batches(

        values=contents,

        batch_size=batch_size,

    )

    extracted_batches = []

    for batch_index, content_batch in enumerate(
        content_batches,
        start=1,
    ):

        extraction = _extract_batch(

            request=request,

            contents=content_batch,

            model=model,

            max_attempts=max_attempts,

        )

        extracted_batches.append(

            _prefix_extraction_ids(

                extraction=extraction,

                batch_index=batch_index,

            )

        )

    return extracted_batches
