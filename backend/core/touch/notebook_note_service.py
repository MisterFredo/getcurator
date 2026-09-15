from typing import (
    Any,
    Optional,
)

from pydantic import (
    BaseModel,
    Field,
)

from core.touch.notebook_models import (
    TouchEvidenceNote,
    TouchNotebookRequest,
)

from core.touch.notebook_note_prompt import (
    TOUCH_NOTEBOOK_NOTE_CONSOLIDATION_SYSTEM_PROMPT,
    build_touch_notebook_note_consolidation_prompt,
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
# INTERNAL MODEL
# ============================================================

class TouchNoteConsolidationResult(
    BaseModel,
):

    notes: list[
        TouchEvidenceNote
    ] = Field(
        default_factory=list,
    )

    class Config:

        extra = "forbid"


# ============================================================
# STRING LIST
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

        cleaned_value = (
            value.strip()
        )

        return (
            [cleaned_value]
            if cleaned_value
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
# NORMALIZE NOTE TYPE
# ============================================================

def _normalize_note_type(
    value: Any,
) -> str:

    normalized = (
        str(
            value
            or "FACT"
        )
        .strip()
        .upper()
        .replace(
            " ",
            "_",
        )
        .replace(
            "-",
            "_",
        )
    )

    allowed_values = {
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
    }

    if normalized not in allowed_values:
        return "FACT"

    return normalized


# ============================================================
# NORMALIZE CONFIDENCE
# ============================================================

def _normalize_confidence(
    value: Any,
) -> str:

    normalized = (
        str(
            value
            or "MEDIUM"
        )
        .strip()
        .upper()
    )

    if normalized not in {
        "HIGH",
        "MEDIUM",
        "LOW",
    }:

        return "MEDIUM"

    return normalized


# ============================================================
# NORMALIZE STATUS
# ============================================================

def _normalize_status(
    value: Any,
) -> str:

    normalized = (
        str(
            value
            or "VALIDATED"
        )
        .strip()
        .upper()
        .replace(
            " ",
            "_",
        )
        .replace(
            "-",
            "_",
        )
    )

    if normalized not in {
        "VALIDATED",
        "TO_VERIFY",
        "CONTRADICTED",
    }:

        return "VALIDATED"

    return normalized


# ============================================================
# NORMALIZE RAW NOTE
# ============================================================

def _normalize_raw_note(
    raw_note: Any,
    index: int,
) -> dict:

    if not isinstance(
        raw_note,
        dict,
    ):

        raise ValueError(
            "Une note consolidée n’est pas "
            "un objet JSON"
        )

    note_id = str(
        raw_note.get(
            "note_id"
        )
        or f"note-{index + 1:03d}"
    ).strip()

    statement = str(
        raw_note.get(
            "statement"
        )
        or ""
    ).strip()

    if not statement:

        raise ValueError(
            f"La note {note_id} ne contient "
            "aucun statement"
        )

    input_note_ids = (
        raw_note.get(
            "input_note_ids"
        )
    )

    if input_note_ids is None:

        input_note_ids = (
            raw_note.get(
                "temporary_note_ids"
            )
        )

    if input_note_ids is None:

        input_note_ids = (
            raw_note.get(
                "source_note_ids"
            )
        )

    source_content_ids = (
        raw_note.get(
            "source_content_ids"
        )
    )

    if source_content_ids is None:

        source_content_ids = (
            raw_note.get(
                "content_ids"
            )
        )

    if source_content_ids is None:

        source_content_ids = (
            raw_note.get(
                "source_content_id"
            )
        )

    actors = (
        raw_note.get(
            "actors"
        )
    )

    if actors is None:

        actors = (
            raw_note.get(
                "actor"
            )
        )

    geographies = (
        raw_note.get(
            "geographies"
        )
    )

    if geographies is None:

        geographies = (
            raw_note.get(
                "geography"
            )
        )

    dates = (
        raw_note.get(
            "dates"
        )
    )

    if dates is None:

        dates = (
            raw_note.get(
                "date"
            )
        )

    return {
        "note_id":
            note_id,

        "note_type":
            _normalize_note_type(
                raw_note.get(
                    "note_type"
                )
            ),

        "statement":
            statement,

        "explanation":
            str(
                raw_note.get(
                    "explanation"
                )
                or ""
            ).strip(),

        "actors":
            _normalize_string_list(
                actors
            ),

        "geographies":
            _normalize_string_list(
                geographies
            ),

        "dates":
            _normalize_string_list(
                dates
            ),

        "confidence":
            _normalize_confidence(
                raw_note.get(
                    "confidence"
                )
            ),

        "status":
            _normalize_status(
                raw_note.get(
                    "status"
                )
            ),

        "input_note_ids":
            _normalize_string_list(
                input_note_ids
            ),

        "source_content_ids":
            _normalize_string_list(
                source_content_ids
            ),
    }


# ============================================================
# NORMALIZE PAYLOAD
# ============================================================

def _normalize_payload(
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
            "Le champ notes de la consolidation "
            "doit être une liste"
        )

    return {
        "notes": [

            _normalize_raw_note(
                raw_note=raw_note,
                index=index,
            )

            for index, raw_note in enumerate(
                raw_notes
            )

        ],
    }


# ============================================================
# COLLECT TEMPORARY NOTE IDS
# ============================================================

def _collect_temporary_note_ids(
    extracted_batches: list[dict],
) -> list[str]:

    temporary_note_ids: list[str] = []

    for batch in extracted_batches:

        if not isinstance(
            batch,
            dict,
        ):
            continue

        notes = (
            batch.get(
                "notes",
                [],
            )
            or []
        )

        if not isinstance(
            notes,
            list,
        ):
            continue

        for note in notes:

            if not isinstance(
                note,
                dict,
            ):
                continue

            temporary_note_id = str(
                note.get(
                    "temporary_note_id"
                )
                or note.get(
                    "note_id"
                )
                or ""
            ).strip()

            if temporary_note_id:

                temporary_note_ids.append(
                    temporary_note_id
                )

    unique_temporary_note_ids = (
        unique_ids(
            temporary_note_ids
        )
    )

    if (
        len(unique_temporary_note_ids)
        != len(temporary_note_ids)
    ):

        raise ValueError(
            "Les lots d’extraction contiennent "
            "des temporary_note_id dupliqués"
        )

    if not unique_temporary_note_ids:

        raise ValueError(
            "Aucune note temporaire à consolider"
        )

    return unique_temporary_note_ids

# ============================================================
# COLLECT INPUT NOTES
# ============================================================

def _collect_input_notes_by_id(
    extracted_batches: list[dict],
) -> dict[str, dict]:

    input_notes_by_id: dict[
        str,
        dict,
    ] = {}

    for batch in extracted_batches:

        if not isinstance(
            batch,
            dict,
        ):
            continue

        notes = (
            batch.get(
                "notes",
                [],
            )
            or []
        )

        if not isinstance(
            notes,
            list,
        ):
            continue

        for note in notes:

            if not isinstance(
                note,
                dict,
            ):
                continue

            temporary_note_id = str(
                note.get(
                    "temporary_note_id"
                )
                or ""
            ).strip()

            statement = str(
                note.get(
                    "statement"
                )
                or ""
            ).strip()

            source_content_ids = (
                _normalize_string_list(
                    note.get(
                        "source_content_ids"
                    )
                )
            )

            if (
                not temporary_note_id
                or not statement
            ):

                continue

            if (
                temporary_note_id
                in input_notes_by_id
            ):

                raise ValueError(
                    "Une contribution temporaire "
                    "est dupliquée : "
                    f"{temporary_note_id}"
                )

            input_notes_by_id[
                temporary_note_id
            ] = {
                "statement":
                    statement,

                "source_content_ids":
                    source_content_ids,
            }

    if not input_notes_by_id:

        raise ValueError(
            "Aucune contribution exploitable "
            "à consolider"
        )

    return input_notes_by_id

# ============================================================
# VALIDATE VERBATIM STATEMENTS
# ============================================================

def _validate_verbatim_statements(
    notes: list[TouchEvidenceNote],
    input_notes_by_id: dict[str, dict],
) -> None:

    for note in notes:

        represented_input_notes = [

            input_notes_by_id[
                input_note_id
            ]

            for input_note_id
            in note.input_note_ids

            if (
                input_note_id
                in input_notes_by_id
            )

        ]

        allowed_statements = {

            input_note[
                "statement"
            ]

            for input_note
            in represented_input_notes

        }

        if (
            note.statement
            not in allowed_statements
        ):

            raise ValueError(
                "La consolidation a réécrit "
                "une contribution : "
                f"{note.note_id}"
            )

        expected_source_content_ids = {

            content_id

            for input_note
            in represented_input_notes

            for content_id
            in input_note[
                "source_content_ids"
            ]

        }

        actual_source_content_ids = set(
            note.source_content_ids
        )

        if (
            actual_source_content_ids
            != expected_source_content_ids
        ):

            raise ValueError(
                "La consolidation a modifié "
                "les sources d’une contribution : "
                f"{note.note_id}"
            )

        if note.explanation:

            raise ValueError(
                "La consolidation a ajouté "
                "une explication à une contribution : "
                f"{note.note_id}"
            )


# ============================================================
# VALIDATE CONSOLIDATED NOTES
# ============================================================

def _validate_consolidated_notes(
    notes: list[TouchEvidenceNote],
    temporary_note_ids: list[str],
    allowed_content_ids: set[str],
) -> None:

    if not notes:

        raise ValueError(
            "La consolidation n’a produit "
            "aucune note"
        )

    note_ids = [

        note.note_id

        for note in notes

    ]

    if (
        len(note_ids)
        != len(
            set(
                note_ids
            )
        )
    ):

        raise ValueError(
            "La consolidation contient "
            "des note_id dupliqués"
        )

    expected_temporary_ids = set(
        temporary_note_ids
    )

    placement_counts = {

        temporary_note_id: 0

        for temporary_note_id
        in temporary_note_ids

    }

    unknown_input_note_ids = set()

    unknown_content_ids = set()

    notes_without_inputs = []

    notes_without_sources = []

    for note in notes:

        if not note.input_note_ids:

            notes_without_inputs.append(
                note.note_id
            )

        if not note.source_content_ids:

            notes_without_sources.append(
                note.note_id
            )

        for input_note_id in (
            note.input_note_ids
        ):

            if (
                input_note_id
                not in expected_temporary_ids
            ):

                unknown_input_note_ids.add(
                    input_note_id
                )

                continue

            placement_counts[
                input_note_id
            ] += 1

        for content_id in (
            note.source_content_ids
        ):

            if (
                content_id
                not in allowed_content_ids
            ):

                unknown_content_ids.add(
                    content_id
                )

    if unknown_input_note_ids:

        raise ValueError(
            "La consolidation référence des "
            "notes temporaires inconnues : "
            + ", ".join(
                sorted(
                    unknown_input_note_ids
                )
            )
        )

    if unknown_content_ids:

        raise ValueError(
            "La consolidation référence des "
            "content_id inconnus : "
            + ", ".join(
                sorted(
                    unknown_content_ids
                )
            )
        )

    if notes_without_inputs:

        raise ValueError(
            "Certaines notes consolidées ne "
            "référencent aucune note extraite : "
            + ", ".join(
                sorted(
                    notes_without_inputs
                )
            )
        )

    if notes_without_sources:

        raise ValueError(
            "Certaines notes consolidées ne "
            "référencent aucune source : "
            + ", ".join(
                sorted(
                    notes_without_sources
                )
            )
        )

    invalid_placements = [

        (
            temporary_note_id,
            count,
        )

        for (
            temporary_note_id,
            count,
        ) in placement_counts.items()

        if count != 1

    ]

    if invalid_placements:

        details = "; ".join(

            (
                f"{temporary_note_id} "
                f"(placements={count})"
            )

            for (
                temporary_note_id,
                count,
            ) in invalid_placements

        )

        raise ValueError(
            "Chaque note temporaire doit être "
            "représentée exactement une fois. "
            f"Placements invalides : {details}"
        )


# ============================================================
# CONSOLIDATE NOTES
# ============================================================

def consolidate_notebook_notes(
    request: TouchNotebookRequest,
    extracted_batches: list[dict],
    model: Optional[str] = None,
    max_attempts: int = 2,
) -> list[TouchEvidenceNote]:

    temporary_note_ids = (
        _collect_temporary_note_ids(
            extracted_batches
        )
    )

    allowed_content_ids = set(
        request.content_ids
    )

    original_prompt = (
        build_touch_notebook_note_consolidation_prompt(

            request=request,

            extracted_batches=(
                extracted_batches
            ),

        )
    )

    prompt = original_prompt

    last_error = (
        "Erreur inconnue pendant la "
        "consolidation des notes"
    )

    attempts = max(
        1,
        max_attempts,
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
                    TOUCH_NOTEBOOK_NOTE_CONSOLIDATION_SYSTEM_PROMPT
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
                TouchNoteConsolidationResult
                .model_validate(
                    normalized_payload
                )
            )

            _validate_consolidated_notes(

                notes=result.notes,

                temporary_note_ids=(
                    temporary_note_ids
                ),

                allowed_content_ids=(
                    allowed_content_ids
                ),

            )

            return result.notes

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
        "Échec de la consolidation des notes "
        f"après {attempts} tentative(s) : "
        f"{last_error}"
    )
