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
    TOUCH_NOTEBOOK_NOTE_DEDUPLICATION_SYSTEM_PROMPT,
    build_touch_notebook_note_deduplication_prompt,
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
# INTERNAL MODELS
# ============================================================

class TouchNoteDeduplicationGroup(
    BaseModel,
):

    representative_note_id: str

    note_ids: list[str] = Field(
        default_factory=list,
    )

    class Config:

        extra = "forbid"


class TouchNoteDeduplicationResult(
    BaseModel,
):

    groups: list[
        TouchNoteDeduplicationGroup
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
# NORMALIZE GROUP
# ============================================================

def _normalize_group(
    raw_group: Any,
) -> dict:

    if not isinstance(
        raw_group,
        dict,
    ):

        raise ValueError(
            "Un groupe de déduplication "
            "n’est pas un objet JSON"
        )

    return {

        "representative_note_id":
            str(
                raw_group.get(
                    "representative_note_id"
                )
                or ""
            ).strip(),

        "note_ids":
            _normalize_string_list(
                raw_group.get(
                    "note_ids"
                )
            ),

    }


# ============================================================
# NORMALIZE PAYLOAD
# ============================================================

def _normalize_payload(
    parsed: dict,
) -> dict:

    raw_groups = (
        parsed.get(
            "groups",
            [],
        )
        or []
    )

    if not isinstance(
        raw_groups,
        list,
    ):

        raise ValueError(
            "Le champ groups doit être "
            "une liste"
        )

    return {

        "groups": [

            _normalize_group(
                raw_group
            )

            for raw_group
            in raw_groups

        ],

    }


# ============================================================
# VALIDATE INPUT NOTES
# ============================================================

def _validate_input_notes(
    request: TouchNotebookRequest,
    notes: list[
        TouchEvidenceNote
    ],
) -> dict[str, TouchEvidenceNote]:

    if not notes:

        raise ValueError(
            "Aucune contribution à dédupliquer"
        )

    notes_by_id = {

        note.note_id:
            note

        for note in notes

    }

    if (
        len(notes_by_id)
        != len(notes)
    ):

        raise ValueError(
            "Les contributions contiennent "
            "des note_id dupliqués"
        )

    allowed_content_ids = set(
        request.content_ids
    )

    for note in notes:

        if not note.note_id.strip():

            raise ValueError(
                "Une contribution possède "
                "un note_id vide"
            )

        if not note.statement.strip():

            raise ValueError(
                "Une contribution possède "
                "un statement vide : "
                f"{note.note_id}"
            )

        if not note.source_content_ids:

            raise ValueError(
                "Une contribution ne possède "
                "aucune source : "
                f"{note.note_id}"
            )

        unknown_content_ids = (

            set(
                note.source_content_ids
            )

            - allowed_content_ids

        )

        if unknown_content_ids:

            raise ValueError(
                "Une contribution référence des "
                "contenus extérieurs au corpus : "
                f"{note.note_id} · "
                + ", ".join(
                    sorted(
                        unknown_content_ids
                    )
                )
            )

    return notes_by_id


# ============================================================
# VALIDATE GROUPS
# ============================================================

def _validate_groups(
    result:
        TouchNoteDeduplicationResult,
    notes_by_id:
        dict[str, TouchEvidenceNote],
) -> None:

    if not result.groups:

        raise ValueError(
            "La déduplication n’a produit "
            "aucun groupe"
        )

    expected_note_ids = set(
        notes_by_id
    )

    placement_counts = {

        note_id:
            0

        for note_id
        in expected_note_ids

    }

    unknown_note_ids = set()

    empty_groups = []

    invalid_representatives = []

    for group_index, group in enumerate(
        result.groups,
        start=1,
    ):

        if not group.note_ids:

            empty_groups.append(
                str(
                    group_index
                )
            )

            continue

        if (
            group.representative_note_id
            not in group.note_ids
        ):

            invalid_representatives.append(
                group.representative_note_id
                or f"group-{group_index}"
            )

        for note_id in group.note_ids:

            if (
                note_id
                not in expected_note_ids
            ):

                unknown_note_ids.add(
                    note_id
                )

                continue

            placement_counts[
                note_id
            ] += 1

    if empty_groups:

        raise ValueError(
            "Certains groupes de déduplication "
            "sont vides : "
            + ", ".join(
                empty_groups
            )
        )

    if invalid_representatives:

        raise ValueError(
            "Certains représentants ne sont pas "
            "membres de leur groupe : "
            + ", ".join(
                sorted(
                    invalid_representatives
                )
            )
        )

    if unknown_note_ids:

        raise ValueError(
            "La déduplication référence des "
            "note_id inconnus : "
            + ", ".join(
                sorted(
                    unknown_note_ids
                )
            )
        )

    invalid_placements = [

        (
            note_id,
            count,
        )

        for note_id, count
        in placement_counts.items()

        if count != 1

    ]

    if invalid_placements:

        details = "; ".join(

            (
                f"{note_id} "
                f"(placements={count})"
            )

            for note_id, count
            in sorted(
                invalid_placements
            )

        )

        raise ValueError(
            "Chaque contribution doit apparaître "
            "exactement une fois. "
            f"Placements invalides : {details}"
        )


# ============================================================
# MERGE CONFIDENCE
# ============================================================

def _merge_confidence(
    notes: list[
        TouchEvidenceNote
    ],
) -> str:

    confidence_rank = {
        "LOW": 0,
        "MEDIUM": 1,
        "HIGH": 2,
    }

    return min(

        (
            note.confidence

            for note in notes
        ),

        key=lambda confidence:
            confidence_rank.get(
                confidence,
                1,
            ),

    )


# ============================================================
# MERGE STATUS
# ============================================================

def _merge_status(
    notes: list[
        TouchEvidenceNote
    ],
) -> str:

    statuses = {

        note.status

        for note in notes

    }

    if (
        "CONTRADICTED"
        in statuses
    ):

        return "CONTRADICTED"

    if (
        "TO_VERIFY"
        in statuses
    ):

        return "TO_VERIFY"

    return "VALIDATED"


# ============================================================
# BUILD DEDUPLICATED NOTES
# ============================================================

def _build_deduplicated_notes(
    result:
        TouchNoteDeduplicationResult,
    original_notes: list[
        TouchEvidenceNote
    ],
    notes_by_id:
        dict[str, TouchEvidenceNote],
) -> list[TouchEvidenceNote]:

    original_position = {

        note.note_id:
            index

        for index, note
        in enumerate(
            original_notes
        )

    }

    ordered_groups = sorted(

        result.groups,

        key=lambda group:
            min(

                original_position[
                    note_id
                ]

                for note_id
                in group.note_ids

            ),

    )

    deduplicated_notes = []

    for note_index, group in enumerate(
        ordered_groups,
        start=1,
    ):

        member_notes = [

            notes_by_id[
                note_id
            ]

            for note_id
            in group.note_ids

        ]

        representative = notes_by_id[
            group.representative_note_id
        ]

        input_note_ids = unique_ids([

            input_note_id

            for note in member_notes

            for input_note_id
            in note.input_note_ids

        ])

        source_content_ids = unique_ids([

            content_id

            for note in member_notes

            for content_id
            in note.source_content_ids

        ])

        actors = unique_ids([

            actor

            for note in member_notes

            for actor
            in note.actors

        ])

        geographies = unique_ids([

            geography

            for note in member_notes

            for geography
            in note.geographies

        ])

        dates = unique_ids([

            date

            for note in member_notes

            for date
            in note.dates

        ])

        deduplicated_notes.append(

            representative.model_copy(
                update={

                    "note_id":
                        f"note-{note_index:03d}",

                    "input_note_ids":
                        input_note_ids,

                    # The representative statement is copied
                    # verbatim from an original contribution.
                    "statement":
                        representative.statement,

                    "explanation":
                        "",

                    "actors":
                        actors,

                    "geographies":
                        geographies,

                    "dates":
                        dates,

                    "confidence":
                        _merge_confidence(
                            member_notes
                        ),

                    "status":
                        _merge_status(
                            member_notes
                        ),

                    "source_content_ids":
                        source_content_ids,

                },
            )

        )

    return deduplicated_notes


# ============================================================
# DEDUPLICATE NOTEBOOK NOTES
# ============================================================

def deduplicate_notebook_notes(
    request: TouchNotebookRequest,
    notes: list[
        TouchEvidenceNote
    ],
    model: Optional[str] = None,
    max_attempts: int = 2,
) -> list[TouchEvidenceNote]:

    notes_by_id = (
        _validate_input_notes(
            request=request,
            notes=notes,
        )
    )

    if len(notes) == 1:

        return [

            notes[0].model_copy(
                update={
                    "note_id":
                        "note-001",
                },
            )

        ]

    original_prompt = (
        build_touch_notebook_note_deduplication_prompt(

            request=request,

            notes=notes,

        )
    )

    prompt = original_prompt

    attempts = max(
        1,
        max_attempts,
    )

    last_error = (
        "Erreur inconnue pendant la "
        "déduplication des contributions"
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
                    TOUCH_NOTEBOOK_NOTE_DEDUPLICATION_SYSTEM_PROMPT
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
                TouchNoteDeduplicationResult
                .model_validate(
                    normalized_payload
                )
            )

            _validate_groups(
                result=result,
                notes_by_id=notes_by_id,
            )

            return _build_deduplicated_notes(

                result=result,

                original_notes=notes,

                notes_by_id=notes_by_id,

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
        "Échec de la déduplication des "
        "contributions après "
        f"{attempts} tentative(s) : "
        f"{last_error}"
    )
