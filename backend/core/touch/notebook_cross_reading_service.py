import re

from typing import (
    Any,
    Optional,
)

from pydantic import (
    BaseModel,
    Field,
)

from core.touch.notebook_cross_reading_prompt import (
    TOUCH_NOTEBOOK_CROSS_READING_SYSTEM_PROMPT,
    build_touch_notebook_cross_reading_prompt,
)

from core.touch.notebook_models import (
    TouchCorpusNotebook,
    TouchCrossReadingType,
    TouchEvidenceConfidence,
    TouchNotebookCrossReading,
    TouchNotebookRequest,
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
# CONFIGURATION
# ============================================================

MAX_TOUCH_CROSS_READINGS = 6

MAX_TOUCH_CROSS_READING_WORDS = 90

MULTI_NOTE_READING_TYPES = {

    "CONVERGENCE",

    "DIFFERENCE",

    "ENABLING_CONDITION",

    "FRICTION",

}


# ============================================================
# INTERNAL MODELS
# ============================================================

class TouchNotebookCrossReadingDraft(
    BaseModel,
):

    title: str

    statement: str

    reading_type: TouchCrossReadingType

    note_ids: list[str] = Field(
        default_factory=list,
    )

    confidence: TouchEvidenceConfidence

    class Config:

        extra = "forbid"


class TouchNotebookCrossReadingResult(
    BaseModel,
):

    readings: list[
        TouchNotebookCrossReadingDraft
    ] = Field(
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
# NORMALIZE DRAFT
# ============================================================

def _normalize_draft(
    raw_reading: Any,
) -> dict:

    if not isinstance(
        raw_reading,
        dict,
    ):

        raise ValueError(
            "Une lecture croisée Touch "
            "n’est pas un objet JSON"
        )

    return {

        "title":
            str(
                raw_reading.get(
                    "title"
                )
                or ""
            ).strip(),

        "statement":
            str(
                raw_reading.get(
                    "statement"
                )
                or ""
            ).strip(),

        "reading_type":
            str(
                raw_reading.get(
                    "reading_type"
                )
                or ""
            )
            .strip()
            .upper(),

        "note_ids":
            _normalize_string_list(
                raw_reading.get(
                    "note_ids"
                )
            ),

        "confidence":
            str(
                raw_reading.get(
                    "confidence"
                )
                or ""
            )
            .strip()
            .upper(),

    }


# ============================================================
# NORMALIZE PAYLOAD
# ============================================================

def _normalize_payload(
    parsed: dict,
) -> dict:

    raw_readings = (
        parsed.get(
            "readings",
            [],
        )
        or []
    )

    if not isinstance(
        raw_readings,
        list,
    ):

        raise ValueError(
            "Le champ readings des lectures "
            "croisées doit être une liste"
        )

    return {

        "readings": [

            _normalize_draft(
                raw_reading
            )

            for raw_reading
            in raw_readings

        ],

    }


# ============================================================
# COUNT WORDS
# ============================================================

def _count_words(
    value: str,
) -> int:

    words = re.findall(
        (
            r"\b[\wÀ-ÖØ-öø-ÿ]+"
            r"(?:[’'-][\wÀ-ÖØ-öø-ÿ]+)*\b"
        ),
        value,
    )

    return len(
        words
    )


# ============================================================
# VALIDATE CROSS READINGS
# ============================================================

def _validate_cross_readings(
    result: TouchNotebookCrossReadingResult,
    notebook: TouchCorpusNotebook,
) -> None:

    if len(
        result.readings
    ) > MAX_TOUCH_CROSS_READINGS:

        raise ValueError(
            "Le moteur Touch a retourné plus de "
            f"{MAX_TOUCH_CROSS_READINGS} lectures "
            "croisées"
        )

    available_note_ids = {

        note.note_id

        for note in notebook.notes

    }

    unknown_note_ids = set()

    incomplete_indexes = []

    insufficient_note_indexes = []

    invalid_length_indexes = []

    duplicated_statements = set()

    seen_statements = set()

    for reading_index, reading in enumerate(
        result.readings,
        start=1,
    ):

        if (
            not reading.title
            or not reading.statement
            or not reading.note_ids
        ):

            incomplete_indexes.append(
                str(
                    reading_index
                )
            )

            continue

        statement_key = (
            reading.statement
            .strip()
            .casefold()
        )

        if statement_key in seen_statements:

            duplicated_statements.add(
                str(
                    reading_index
                )
            )

        seen_statements.add(
            statement_key
        )

        word_count = _count_words(
            reading.statement
        )

        if (
            word_count
            > MAX_TOUCH_CROSS_READING_WORDS
        ):

            invalid_length_indexes.append(
                (
                    reading_index,
                    word_count,
                )
            )

        if (
            reading.reading_type
            in MULTI_NOTE_READING_TYPES
            and len(
                reading.note_ids
            ) < 2
        ):

            insufficient_note_indexes.append(
                str(
                    reading_index
                )
            )

        for note_id in reading.note_ids:

            if (
                note_id
                not in available_note_ids
            ):

                unknown_note_ids.add(
                    note_id
                )

    if incomplete_indexes:

        raise ValueError(
            "Certaines lectures croisées Touch "
            "sont incomplètes : "
            + ", ".join(
                incomplete_indexes
            )
        )

    if insufficient_note_indexes:

        raise ValueError(
            "Certaines lectures croisées doivent "
            "référencer au moins deux notes : "
            + ", ".join(
                insufficient_note_indexes
            )
        )

    if invalid_length_indexes:

        details = "; ".join(

            (
                f"reading-{reading_index} "
                f"({word_count} mots)"
            )

            for (
                reading_index,
                word_count,
            )
            in invalid_length_indexes

        )

        raise ValueError(
            "Certaines lectures croisées sont "
            "trop longues : "
            f"{details}"
        )

    if unknown_note_ids:

        raise ValueError(
            "Les lectures croisées référencent "
            "des note_id inconnus : "
            + ", ".join(
                sorted(
                    unknown_note_ids
                )
            )
        )

    if duplicated_statements:

        raise ValueError(
            "Certaines lectures croisées sont "
            "dupliquées : "
            + ", ".join(
                sorted(
                    duplicated_statements
                )
            )
        )


# ============================================================
# BUILD CROSS READING ITEMS
# ============================================================

def _build_cross_reading_items(
    result: TouchNotebookCrossReadingResult,
    notebook: TouchCorpusNotebook,
) -> list[
    TouchNotebookCrossReading
]:

    notes_by_id = {

        note.note_id:
            note

        for note in notebook.notes

    }

    cross_readings = []

    for reading_index, reading in enumerate(
        result.readings,
        start=1,
    ):

        note_ids = unique_ids(
            reading.note_ids
        )

        source_content_ids = unique_ids([

            content_id

            for note_id in note_ids

            for content_id in (
                notes_by_id[
                    note_id
                ].source_content_ids
            )

        ])

        cross_readings.append(

            TouchNotebookCrossReading(

                reading_id=(
                    f"reading-{reading_index:03d}"
                ),

                title=(
                    reading.title.strip()
                ),

                statement=(
                    reading.statement.strip()
                ),

                reading_type=(
                    reading.reading_type
                ),

                note_ids=note_ids,

                source_content_ids=(
                    source_content_ids
                ),

                confidence=(
                    reading.confidence
                ),

            )

        )

    return cross_readings


# ============================================================
# BUILD NOTEBOOK CROSS READINGS
# ============================================================

def build_notebook_cross_readings(
    request: TouchNotebookRequest,
    notebook: TouchCorpusNotebook,
    model: Optional[str] = None,
    max_attempts: int = 2,
) -> TouchCorpusNotebook:

    report_archetype = (
        request
        .report_design
        .report_archetype
    )

    if report_archetype not in (
        "COMPARATIVE_ANALYSIS",
        "CROSS_CONTEXT_ANALYSIS",
    ):

        return notebook.model_copy(
            update={
                "cross_readings": [],
            },
        )

    if not notebook.notes:

        return notebook.model_copy(
            update={
                "cross_readings": [],
            },
        )

    original_prompt = (
        build_touch_notebook_cross_reading_prompt(

            request=request,

            notebook=notebook,

        )
    )

    prompt = original_prompt

    attempts = max(
        1,
        max_attempts,
    )

    last_error = (
        "Erreur inconnue pendant la génération "
        "des lectures croisées Touch"
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
                    TOUCH_NOTEBOOK_CROSS_READING_SYSTEM_PROMPT
                ),

            )

            parsed = extract_json_object(
                raw_content
            )

            normalized_payload = (
                _normalize_payload(
                    parsed
                )
            )

            result = (
                TouchNotebookCrossReadingResult
                .model_validate(
                    normalized_payload
                )
            )

            _validate_cross_readings(

                result=result,

                notebook=notebook,

            )

            cross_readings = (
                _build_cross_reading_items(

                    result=result,

                    notebook=notebook,

                )
            )

            return notebook.model_copy(
                update={

                    "cross_readings":
                        cross_readings,

                },
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
        "Échec de la génération des lectures "
        "croisées Touch après "
        f"{attempts} tentative(s) : "
        f"{last_error}"
    )
