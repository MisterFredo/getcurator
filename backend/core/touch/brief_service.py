import json

from typing import (
    Optional,
)

from core.touch.brief_models import (
    TouchBriefOutcome,
    TouchBriefRequest,
    TouchBriefStructure,
)

from core.touch.brief_prompt import (
    TOUCH_BRIEF_SYSTEM_PROMPT,
    build_touch_brief_prompt,
)

from utils.llm import (
    run_llm_json,
)


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_TOUCH_BRIEF_ATTEMPTS = 2


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
            "d’organisation Touch"
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
                "la réponse du brief Touch"
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
                "le moteur du brief Touch"
            ) from exc

    if not isinstance(
        parsed,
        dict,
    ):

        raise ValueError(
            "La réponse du brief Touch "
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
# UNIQUE STRINGS
# ============================================================

def _unique_strings(
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

Correct the brief structure.

Use only identifiers supplied in the notebook.

Select only the notebook notes and certified Numbers that are
useful for the assisted interpretation.

The backend automatically classifies every unselected note and
Number as hidden.

Do not invent or modify identifiers.

Return only the corrected JSON object.
""".strip()


# ============================================================
# NORMALIZE BRIEF
# ============================================================

def _normalize_brief(
    brief: TouchBriefStructure,
) -> TouchBriefStructure:

    sections = []

    for section in brief.sections:

        groups = [

            group.model_copy(
                update={

                    "label":
                        group.label.strip(),

                    "note_ids":
                        _unique_strings(
                            group.note_ids
                        ),

                    "number_ids":
                        _unique_strings(
                            group.number_ids
                        ),

                    "event_ids":
                        _unique_strings(
                            group.event_ids
                        ),

                },
            )

            for group in section.groups

        ]

        sections.append(

            section.model_copy(
                update={

                    "section_id":
                        section.section_id.strip(),

                    "title":
                        section.title.strip(),

                    "introduction":
                        section.introduction.strip(),

                    "note_ids":
                        _unique_strings(
                            section.note_ids
                        ),

                    "number_ids":
                        _unique_strings(
                            section.number_ids
                        ),

                    "event_ids":
                        _unique_strings(
                            section.event_ids
                        ),

                    "groups":
                        groups,

                },
            )

        )

    return brief.model_copy(
        update={

            "recommendation_reason":
                brief.recommendation_reason.strip(),

            "headline":
                brief.headline.strip(),

            "subheadline":
                brief.subheadline.strip(),

            "central_question":
                brief.central_question.strip(),

            "key_message":
                brief.key_message.strip(),

            "sections":
                sections,

            "hidden_note_ids":
                _unique_strings(
                    brief.hidden_note_ids
                ),

            "hidden_number_ids":
                _unique_strings(
                    brief.hidden_number_ids
                ),

            "editorial_cautions":
                _unique_strings(
                    brief.editorial_cautions
                ),

        },
    )


# ============================================================
# VALIDATE SECTION IDS
# ============================================================

def _validate_section_ids(
    brief: TouchBriefStructure,
) -> None:

    section_ids = [

        section.section_id

        for section in brief.sections

    ]

    if any(
        not section_id
        for section_id in section_ids
    ):

        raise ValueError(
            "Le brief contient un section_id vide"
        )

    if len(
        section_ids
    ) != len(
        set(
            section_ids
        )
    ):

        raise ValueError(
            "Le brief contient des section_id "
            "dupliqués"
        )


# ============================================================
# COLLECT VISIBLE REFERENCES
# ============================================================

def _collect_visible_references(
    brief: TouchBriefStructure,
) -> tuple[
    list[str],
    list[str],
    list[str],
]:

    note_ids = []

    number_ids = []

    event_ids = []

    for section in brief.sections:

        note_ids.extend(
            section.note_ids
        )

        number_ids.extend(
            section.number_ids
        )

        event_ids.extend(
            section.event_ids
        )

        for group in section.groups:

            note_ids.extend(
                group.note_ids
            )

            number_ids.extend(
                group.number_ids
            )

            event_ids.extend(
                group.event_ids
            )

    return (
        note_ids,
        number_ids,
        event_ids,
    )

# ============================================================
# SYNCHRONIZE HIDDEN REFERENCES
# ============================================================

def _synchronize_hidden_references(
    request: TouchBriefRequest,
    brief: TouchBriefStructure,
) -> TouchBriefStructure:

    (
        visible_note_ids,
        visible_number_ids,
        _,
    ) = _collect_visible_references(
        brief
    )

    visible_note_id_set = set(
        visible_note_ids
    )

    visible_number_id_set = set(
        visible_number_ids
    )

    hidden_note_ids = [

        note.note_id

        for note in request.notebook.notes

        if (
            note.note_id
            not in visible_note_id_set
        )

    ]

    hidden_number_ids = [

        number.number_id

        for number
        in request.notebook.validated_numbers

        if (
            number.number_id
            not in visible_number_id_set
        )

    ]

    return brief.model_copy(
        update={
            "hidden_note_ids":
                hidden_note_ids,

            "hidden_number_ids":
                hidden_number_ids,
        },
    )


# ============================================================
# VALIDATE REFERENCES
# ============================================================

def _validate_references(
    request: TouchBriefRequest,
    brief: TouchBriefStructure,
) -> None:

    notebook = request.notebook

    allowed_note_ids = {

        note.note_id

        for note in notebook.notes

    }

    allowed_number_ids = {

        number.number_id

        for number in notebook.validated_numbers

    }

    allowed_event_ids = {

        event.event_id

        for event in notebook.events

    }

    (
        visible_note_ids,
        visible_number_ids,
        visible_event_ids,
    ) = _collect_visible_references(
        brief
    )

    referenced_note_ids = (

        set(
            visible_note_ids
        )

        | set(
            brief.hidden_note_ids
        )

    )

    referenced_number_ids = (

        set(
            visible_number_ids
        )

        | set(
            brief.hidden_number_ids
        )

    )

    unknown_note_ids = (

        referenced_note_ids
        - allowed_note_ids

    )

    if unknown_note_ids:

        raise ValueError(
            "Le brief référence des note_ids "
            "inconnus : "
            + ", ".join(
                sorted(
                    unknown_note_ids
                )
            )
        )

    unknown_number_ids = (

        referenced_number_ids
        - allowed_number_ids

    )

    if unknown_number_ids:

        raise ValueError(
            "Le brief référence des number_ids "
            "inconnus : "
            + ", ".join(
                sorted(
                    unknown_number_ids
                )
            )
        )

    unknown_event_ids = (

        set(
            visible_event_ids
        )

        - allowed_event_ids

    )

    if unknown_event_ids:

        raise ValueError(
            "Le brief référence des event_ids "
            "inconnus : "
            + ", ".join(
                sorted(
                    unknown_event_ids
                )
            )
        )

    missing_note_ids = (

        allowed_note_ids
        - referenced_note_ids

    )

    if missing_note_ids:

        raise ValueError(
            "Certaines notes du notebook ne sont "
            "ni affichées ni masquées : "
            + ", ".join(
                sorted(
                    missing_note_ids
                )
            )
        )

    missing_number_ids = (

        allowed_number_ids
        - referenced_number_ids

    )

    if missing_number_ids:

        raise ValueError(
            "Certains chiffres validés ne sont "
            "ni affichés ni masqués : "
            + ", ".join(
                sorted(
                    missing_number_ids
                )
            )
        )

    visible_and_hidden_notes = (

        set(
            visible_note_ids
        )

        & set(
            brief.hidden_note_ids
        )

    )

    if visible_and_hidden_notes:

        raise ValueError(
            "Certaines notes sont à la fois "
            "affichées et masquées : "
            + ", ".join(
                sorted(
                    visible_and_hidden_notes
                )
            )
        )

    visible_and_hidden_numbers = (

        set(
            visible_number_ids
        )

        & set(
            brief.hidden_number_ids
        )

    )

    if visible_and_hidden_numbers:

        raise ValueError(
            "Certains chiffres sont à la fois "
            "affichés et masqués : "
            + ", ".join(
                sorted(
                    visible_and_hidden_numbers
                )
            )
        )


# ============================================================
# VALIDATE DUPLICATE NOTES
# ============================================================

def _validate_duplicate_notes(
    brief: TouchBriefStructure,
) -> None:

    note_sections: dict[
        str,
        list[str],
    ] = {}

    for section in brief.sections:

        section_note_ids = list(
            section.note_ids
        )

        for group in section.groups:

            section_note_ids.extend(
                group.note_ids
            )

        for note_id in set(
            section_note_ids
        ):

            if note_id not in note_sections:

                note_sections[
                    note_id
                ] = []

            note_sections[
                note_id
            ].append(
                section.section_type
            )

    invalid_duplicates = []

    for (
        note_id,
        section_types,
    ) in note_sections.items():

        if len(
            section_types
        ) <= 1:

            continue

        if (
            len(
                section_types
            ) == 2
            and "ESSENTIAL" in section_types
        ):

            continue

        invalid_duplicates.append(
            note_id
        )

    if invalid_duplicates:

        raise ValueError(
            "Certaines notes sont répétées dans "
            "plusieurs sections sans justification : "
            + ", ".join(
                sorted(
                    invalid_duplicates
                )
            )
        )


# ============================================================
# VALIDATE GROUPS
# ============================================================

def _validate_groups(
    brief: TouchBriefStructure,
) -> None:

    for section in brief.sections:

        if (
            section.layout == "COLUMNS"
            and not section.groups
        ):

            raise ValueError(
                "Une section en colonnes doit "
                "contenir des groupes"
            )

        for group in section.groups:

            if not group.label:

                raise ValueError(
                    "Un groupe du brief possède "
                    "un libellé vide"
                )

            if not (
                group.note_ids
                or group.number_ids
                or group.event_ids
            ):

                raise ValueError(
                    "Un groupe du brief ne contient "
                    "aucun élément"
                )


# ============================================================
# VALIDATE REQUIRED CONTENT
# ============================================================

def _validate_required_content(
    brief: TouchBriefStructure,
) -> None:

    if not brief.headline:

        raise ValueError(
            "Le brief ne possède pas de titre"
        )

    if not brief.central_question:

        raise ValueError(
            "Le brief ne possède pas de "
            "question centrale"
        )

    if not brief.key_message:

        raise ValueError(
            "Le brief ne possède pas de "
            "message central"
        )

    if not brief.sections:

        raise ValueError(
            "Le brief ne contient aucune section"
        )

    for section in brief.sections:

        if not section.title:

            raise ValueError(
                "Une section du brief possède "
                "un titre vide"
            )

        if not (
            section.note_ids
            or section.number_ids
            or section.event_ids
            or section.groups
        ):

            raise ValueError(
                "Une section du brief ne contient "
                "aucun élément"
            )


# ============================================================
# VALIDATE BRIEF
# ============================================================

def _validate_brief(
    request: TouchBriefRequest,
    brief: TouchBriefStructure,
) -> None:

    _validate_section_ids(
        brief
    )

    _validate_required_content(
        brief
    )

    _validate_groups(
        brief
    )

    _validate_references(
        request=request,
        brief=brief,
    )

    _validate_duplicate_notes(
        brief
    )

# ============================================================
# BUILD TOUCH BRIEF
# ============================================================

def build_touch_brief(
    request: TouchBriefRequest,
    model: Optional[str] = None,
) -> TouchBriefOutcome:

    try:

        normalized_request = (
            request.model_copy(
                update={
                    "editorial_instruction":
                        request
                        .editorial_instruction
                        .strip(),

                    "output_language":
                        _normalize_language(
                            request.output_language
                        ),
                },
            )
        )

        original_prompt = (
            build_touch_brief_prompt(
                request=normalized_request,
            )
        )

        prompt = original_prompt

        last_error = (
            "Erreur inconnue du moteur "
            "d’organisation Touch"
        )

        for attempt in range(
            DEFAULT_TOUCH_BRIEF_ATTEMPTS
        ):

            try:

                raw_content = run_llm_json(

                    prompt=prompt,

                    model=model,

                    temperature=0.0,

                    system_prompt=(
                        TOUCH_BRIEF_SYSTEM_PROMPT
                    ),

                )

                parsed = _extract_json_object(
                    raw_content
                )

                brief = (
                    TouchBriefStructure
                    .model_validate(
                        parsed
                    )
                )

                brief = _normalize_brief(
                    brief
                )

                brief = (
                    _synchronize_hidden_references(

                        request=(
                            normalized_request
                        ),

                        brief=brief,

                    )
                )

                _validate_brief(

                    request=(
                        normalized_request
                    ),

                    brief=brief,

                )

                return TouchBriefOutcome(

                    status="GENERATED",

                    brief=brief,

                    error=None,

                )

            except Exception as exc:

                last_error = str(
                    exc
                )

                if (
                    attempt + 1
                    >= DEFAULT_TOUCH_BRIEF_ATTEMPTS
                ):

                    break

                prompt = _build_retry_prompt(

                    original_prompt=(
                        original_prompt
                    ),

                    error=last_error,

                )

        raise ValueError(
            "Échec de l’organisation du brief "
            f"après "
            f"{DEFAULT_TOUCH_BRIEF_ATTEMPTS} "
            "tentative(s) : "
            f"{last_error}"
        )

    except Exception as exc:

        return TouchBriefOutcome(

            status="GENERATION_FAILED",

            brief=None,

            error=str(
                exc
            )[:2000],

        )
