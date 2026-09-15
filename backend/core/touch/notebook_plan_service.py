from datetime import (
    datetime,
)

from core.touch.notebook_models import (
    TouchCorpusNotebook,
    TouchNotebookSection,
)

from core.touch.notebook_utils import (
    unique_ids,
)


# ============================================================
# NORMALIZE NOTEBOOK
# ============================================================

def normalize_notebook(
    notebook: TouchCorpusNotebook,
) -> TouchCorpusNotebook:

    notes = [
        note.model_copy(
            update={
                "note_id":
                    note.note_id.strip(),

                "input_note_ids":
                    unique_ids(
                        note.input_note_ids
                    ),

                "statement":
                    note.statement.strip(),

                "explanation":
                    (
                        note.explanation.strip()
                        if note.explanation
                        else ""
                    ),

                "actors":
                    unique_ids(
                        note.actors
                    ),

                "geographies":
                    unique_ids(
                        note.geographies
                    ),

                "dates":
                    unique_ids(
                        note.dates
                    ),

                "source_content_ids":
                    unique_ids(
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
                    (
                        event.description.strip()
                        if event.description
                        else ""
                    ),

                "event_date":
                    (
                        event.event_date.strip()
                        if event.event_date
                        else None
                    ),

                "actors":
                    unique_ids(
                        event.actors
                    ),

                "note_ids":
                    unique_ids(
                        event.note_ids
                    ),

                "number_ids":
                    unique_ids(
                        event.number_ids
                    ),

                "source_content_ids":
                    unique_ids(
                        event.source_content_ids
                    ),
            },
        )
        for event in notebook.events
    ]

    sections = [
        section.model_copy(
            update={
                "section_id":
                    section.section_id.strip(),

                "title":
                    section.title.strip(),

                "description":
                    (
                        section.description.strip()
                        if section.description
                        else ""
                    ),

                "event_ids":
                    unique_ids(
                        section.event_ids
                    ),

                "note_ids":
                    unique_ids(
                        section.note_ids
                    ),

                "number_ids":
                    unique_ids(
                        section.number_ids
                    ),
            },
        )
        for section in notebook.sections
    ]

    timeline = [
        item.model_copy(
            update={
                "date":
                    item.date.strip(),

                "label":
                    item.label.strip(),

                "description":
                    (
                        item.description.strip()
                        if item.description
                        else ""
                    ),

                "event_id":
                    (
                        item.event_id.strip()
                        if item.event_id
                        else None
                    ),

                "note_ids":
                    unique_ids(
                        item.note_ids
                    ),

                "source_content_ids":
                    unique_ids(
                        item.source_content_ids
                    ),
            },
        )
        for item in notebook.timeline
    ]

    validated_numbers = [
        number.model_copy(
            update={
                "number_id":
                    number.number_id.strip(),

                "id_content":
                    number.id_content.strip(),

                "source_content_ids":
                    unique_ids(
                        number.source_content_ids
                    ),
            },
        )
        for number in notebook.validated_numbers
    ]

    contradictions = [
        contradiction.model_copy(
            update={
                "subject":
                    contradiction.subject.strip(),

                "description":
                    contradiction.description.strip(),

                "note_ids":
                    unique_ids(
                        contradiction.note_ids
                    ),

                "source_content_ids":
                    unique_ids(
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

            "sections":
                sections,

            "notes":
                notes,

            "events":
                events,

            "timeline":
                timeline,

            "dimensions":
                [],

            "validated_numbers":
                validated_numbers,

            "quarantined_numbers":
                [],

            "contradictions":
                contradictions,

            "corpus_strengths":
                unique_ids(
                    notebook.corpus_strengths
                ),

            "corpus_limits":
                unique_ids(
                    notebook.corpus_limits
                ),
        },
    )


# ============================================================
# TIMELINE SORT KEY
# ============================================================

def _timeline_sort_key(
    value: str,
) -> tuple[int, datetime]:

    normalized_value = (
        value
        or ""
    ).strip()

    formats = (
        "%Y-%m-%d",
        "%Y-%m",
        "%Y",
    )

    for date_format in formats:

        try:

            return (
                0,
                datetime.strptime(
                    normalized_value,
                    date_format,
                ),
            )

        except ValueError:

            continue

    return (
        1,
        datetime.max,
    )


# ============================================================
# EVENT SOURCES
# ============================================================

def _get_event_sources(
    event,
    notes_by_id: dict,
    numbers_by_id: dict,
) -> set[str]:

    source_ids = set(
        event.source_content_ids
    )

    for note_id in event.note_ids:

        note = notes_by_id.get(
            note_id
        )

        if note:

            source_ids.update(
                note.source_content_ids
            )

    for number_id in event.number_ids:

        number = numbers_by_id.get(
            number_id
        )

        if number:

            source_ids.update(
                number.source_content_ids
            )

    return source_ids


# ============================================================
# SECTION SOURCES
# ============================================================

def _get_section_sources(
    section,
    events_by_id: dict,
    notes_by_id: dict,
    numbers_by_id: dict,
) -> set[str]:

    source_ids: set[str] = set()

    for event_id in section.event_ids:

        event = events_by_id.get(
            event_id
        )

        if event:

            source_ids.update(
                _get_event_sources(

                    event=event,

                    notes_by_id=(
                        notes_by_id
                    ),

                    numbers_by_id=(
                        numbers_by_id
                    ),

                )
            )

    for note_id in section.note_ids:

        note = notes_by_id.get(
            note_id
        )

        if note:

            source_ids.update(
                note.source_content_ids
            )

    for number_id in section.number_ids:

        number = numbers_by_id.get(
            number_id
        )

        if number:

            source_ids.update(
                number.source_content_ids
            )

    return source_ids


# ============================================================
# FIND BEST SECTION
# ============================================================

def _find_best_section_index(
    item_source_ids: set[str],
    sections: list[
        TouchNotebookSection
    ],
    events_by_id: dict,
    notes_by_id: dict,
    numbers_by_id: dict,
) -> int | None:

    if not item_source_ids:
        return None

    best_index = None
    best_score = 0

    for index, section in enumerate(
        sections
    ):

        section_source_ids = (
            _get_section_sources(

                section=section,

                events_by_id=(
                    events_by_id
                ),

                notes_by_id=(
                    notes_by_id
                ),

                numbers_by_id=(
                    numbers_by_id
                ),

            )
        )

        score = len(
            item_source_ids
            & section_source_ids
        )

        if score > best_score:

            best_index = index
            best_score = score

    return best_index


# ============================================================
# ATTACH ITEM TO SECTION
# ============================================================

def _attach_item_to_section(
    sections: list[
        TouchNotebookSection
    ],
    section_index: int,
    field_name: str,
    item_id: str,
) -> None:

    section = sections[
        section_index
    ]

    current_values = list(
        getattr(
            section,
            field_name,
        )
    )

    current_values.append(
        item_id
    )

    sections[
        section_index
    ] = section.model_copy(
        update={
            field_name:
                unique_ids(
                    current_values
                ),
        },
    )


# ============================================================
# REPAIR DOCUMENTARY PLAN
# ============================================================

def repair_documentary_plan(
    notebook: TouchCorpusNotebook,
) -> TouchCorpusNotebook:

    notes_by_id = {

        note.note_id:
            note

        for note in notebook.notes

    }

    numbers_by_id = {

        number.number_id:
            number

        for number in notebook.validated_numbers

    }

    valid_note_ids = set(
        notes_by_id
    )

    valid_number_ids = set(
        numbers_by_id
    )

    # ========================================================
    # EVENTS
    # ========================================================

    repaired_events = []

    used_event_note_ids: set[str] = set()
    used_event_number_ids: set[str] = set()

    for event in notebook.events:

        note_ids = [

            note_id

            for note_id in event.note_ids

            if (
                note_id in valid_note_ids
                and note_id
                not in used_event_note_ids
            )

        ]

        # An event must be supported by at least one
        # qualitative note. A Number alone is not an event.
        if not note_ids:
            continue

        number_ids = [

            number_id

            for number_id in event.number_ids

            if (
                number_id in valid_number_ids
                and number_id
                not in used_event_number_ids
            )

        ]

        used_event_note_ids.update(
            note_ids
        )

        used_event_number_ids.update(
            number_ids
        )

        repaired_events.append(
            event.model_copy(
                update={
                    "note_ids":
                        note_ids,

                    "number_ids":
                        number_ids,
                },
            )
        )

    events_by_id = {

        event.event_id:
            event

        for event in repaired_events

    }

    valid_event_ids = set(
        events_by_id
    )

    # ========================================================
    # SECTIONS
    # ========================================================

    repaired_sections = []

    used_section_event_ids: set[str] = set()
    used_section_note_ids: set[str] = set()
    used_section_number_ids: set[str] = set()

    for section in notebook.sections:

        event_ids = [

            event_id

            for event_id in section.event_ids

            if (
                event_id in valid_event_ids
                and event_id
                not in used_section_event_ids
            )

        ]

        note_ids = [

            note_id

            for note_id in section.note_ids

            if (
                note_id in valid_note_ids
                and note_id
                not in used_event_note_ids
                and note_id
                not in used_section_note_ids
            )

        ]

        number_ids = [

            number_id

            for number_id in section.number_ids

            if (
                number_id in valid_number_ids
                and number_id
                not in used_event_number_ids
                and number_id
                not in used_section_number_ids
            )

        ]

        if (
            not event_ids
            and not note_ids
            and not number_ids
        ):

            continue

        used_section_event_ids.update(
            event_ids
        )

        used_section_note_ids.update(
            note_ids
        )

        used_section_number_ids.update(
            number_ids
        )

        repaired_sections.append(
            section.model_copy(
                update={
                    "event_ids":
                        event_ids,

                    "note_ids":
                        note_ids,

                    "number_ids":
                        number_ids,
                },
            )
        )

    # ========================================================
    # UNASSIGNED EVENTS
    # ========================================================

    unresolved_event_ids = []

    missing_event_ids = [

        event.event_id

        for event in repaired_events

        if (
            event.event_id
            not in used_section_event_ids
        )

    ]

    for event_id in missing_event_ids:

        event = events_by_id[
            event_id
        ]

        section_index = (
            _find_best_section_index(

                item_source_ids=(
                    _get_event_sources(

                        event=event,

                        notes_by_id=(
                            notes_by_id
                        ),

                        numbers_by_id=(
                            numbers_by_id
                        ),

                    )
                ),

                sections=(
                    repaired_sections
                ),

                events_by_id=(
                    events_by_id
                ),

                notes_by_id=(
                    notes_by_id
                ),

                numbers_by_id=(
                    numbers_by_id
                ),

            )
        )

        if section_index is None:

            unresolved_event_ids.append(
                event_id
            )

            continue

        _attach_item_to_section(

            sections=(
                repaired_sections
            ),

            section_index=(
                section_index
            ),

            field_name="event_ids",

            item_id=event_id,

        )

    # ========================================================
    # UNASSIGNED NOTES
    # ========================================================

    unresolved_note_ids = []

    missing_note_ids = [

        note.note_id

        for note in notebook.notes

        if (
            note.note_id
            not in used_event_note_ids
            and note.note_id
            not in used_section_note_ids
        )

    ]

    for note_id in missing_note_ids:

        note = notes_by_id[
            note_id
        ]

        section_index = (
            _find_best_section_index(

                item_source_ids=set(
                    note.source_content_ids
                ),

                sections=(
                    repaired_sections
                ),

                events_by_id=(
                    events_by_id
                ),

                notes_by_id=(
                    notes_by_id
                ),

                numbers_by_id=(
                    numbers_by_id
                ),

            )
        )

        if section_index is None:

            unresolved_note_ids.append(
                note_id
            )

            continue

        _attach_item_to_section(

            sections=(
                repaired_sections
            ),

            section_index=(
                section_index
            ),

            field_name="note_ids",

            item_id=note_id,

        )

    # ========================================================
    # UNASSIGNED NUMBERS
    # ========================================================

    unresolved_number_ids = []

    missing_number_ids = [

        number.number_id

        for number
        in notebook.validated_numbers

        if (
            number.number_id
            not in used_event_number_ids
            and number.number_id
            not in used_section_number_ids
        )

    ]

    for number_id in missing_number_ids:

        number = numbers_by_id[
            number_id
        ]

        section_index = (
            _find_best_section_index(

                item_source_ids=set(
                    number.source_content_ids
                ),

                sections=(
                    repaired_sections
                ),

                events_by_id=(
                    events_by_id
                ),

                notes_by_id=(
                    notes_by_id
                ),

                numbers_by_id=(
                    numbers_by_id
                ),

            )
        )

        if section_index is None:

            unresolved_number_ids.append(
                number_id
            )

            continue

        _attach_item_to_section(

            sections=(
                repaired_sections
            ),

            section_index=(
                section_index
            ),

            field_name="number_ids",

            item_id=number_id,

        )

    # ========================================================
    # LAST-RESORT SECTION
    # ========================================================

    if (
        unresolved_event_ids
        or unresolved_note_ids
        or unresolved_number_ids
    ):

        existing_section_ids = {

            section.section_id

            for section in repaired_sections

        }

        fallback_section_id = (
            "section-documentary-references"
        )

        suffix = 1

        while (
            fallback_section_id
            in existing_section_ids
        ):

            suffix += 1

            fallback_section_id = (
                "section-documentary-references-"
                f"{suffix}"
            )

        repaired_sections.append(
            TouchNotebookSection(

                section_id=(
                    fallback_section_id
                ),

                title=(
                    "Repères documentaires complémentaires"
                ),

                description=(
                    "Éléments vérifiés du corpus ne partageant "
                    "pas suffisamment de sources avec les "
                    "autres parties du plan."
                ),

                event_ids=(
                    unresolved_event_ids
                ),

                note_ids=(
                    unresolved_note_ids
                ),

                number_ids=(
                    unresolved_number_ids
                ),

            )
        )

    # ========================================================
    # TIMELINE
    # ========================================================

    repaired_timeline = [

        item.model_copy(
            update={
                "event_id":
                    (
                        item.event_id
                        if item.event_id
                        in valid_event_ids
                        else None
                    ),

                "note_ids": [

                    note_id

                    for note_id in item.note_ids

                    if note_id in valid_note_ids

                ],
            },
        )

        for item in notebook.timeline

        if (
            item.date
            and (
                (
                    item.event_id
                    and item.event_id
                    in valid_event_ids
                )
                or any(
                    note_id in valid_note_ids
                    for note_id in item.note_ids
                )
            )
        )

    ]

    repaired_timeline.sort(
        key=lambda item:
            _timeline_sort_key(
                item.date
            )
    )

    # ========================================================
    # CONTRADICTIONS
    # ========================================================

    repaired_contradictions = [

        contradiction.model_copy(
            update={
                "note_ids": [

                    note_id

                    for note_id
                    in contradiction.note_ids

                    if note_id
                    in valid_note_ids

                ],
            },
        )

        for contradiction
        in notebook.contradictions

    ]

    return notebook.model_copy(
        update={
            "sections":
                repaired_sections,

            "events":
                repaired_events,

            "timeline":
                repaired_timeline,

            "dimensions":
                [],

            "quarantined_numbers":
                [],

            "contradictions":
                repaired_contradictions,
        },
    )

# ============================================================
# VALIDATE UNIQUE IDENTIFIERS
# ============================================================

def _validate_unique_identifiers(
    values: list[str],
    label: str,
) -> None:

    if len(values) != len(set(values)):

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
# COUNT REFERENCES
# ============================================================

def _count_references(
    references: list[list[str]],
) -> dict[str, int]:

    counts: dict[str, int] = {}

    for reference_group in references:

        for identifier in reference_group:

            counts[identifier] = (
                counts.get(
                    identifier,
                    0,
                )
                + 1
            )

    return counts


# ============================================================
# VALIDATE NOTEBOOK
# ============================================================

def validate_notebook(
    notebook: TouchCorpusNotebook,
    allowed_content_ids: set[str],
) -> None:

    section_ids = [
        section.section_id
        for section in notebook.sections
    ]

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
        section_ids,
        "section_id",
    )

    _validate_unique_identifiers(
        note_ids,
        "note_id",
    )

    _validate_unique_identifiers(
        event_ids,
        "event_id",
    )

    _validate_unique_identifiers(
        number_ids,
        "number_id",
    )

    note_id_set = set(note_ids)
    event_id_set = set(event_ids)
    number_id_set = set(number_ids)

    if not notebook.sections:

        raise ValueError(
            "Le notebook ne contient aucune "
            "section documentaire"
        )

    referenced_source_ids = set()

    # ========================================================
    # SOURCES
    # ========================================================

    for note in notebook.notes:

        if not note.source_content_ids:

            raise ValueError(
                "Une note ne possède aucune source : "
                f"{note.note_id}"
            )

        referenced_source_ids.update(
            note.source_content_ids
        )

    for number in notebook.validated_numbers:

        if (
            number.id_content
            not in allowed_content_ids
        ):

            raise ValueError(
                "Un Number référence un contenu "
                "extérieur au corpus : "
                f"{number.number_id}"
            )

        if not number.source_content_ids:

            raise ValueError(
                "Un Number ne possède aucune source : "
                f"{number.number_id}"
            )

        referenced_source_ids.update(
            number.source_content_ids
        )

    for event in notebook.events:

        referenced_source_ids.update(
            event.source_content_ids
        )

    for item in notebook.timeline:

        referenced_source_ids.update(
            item.source_content_ids
        )

    for contradiction in notebook.contradictions:

        referenced_source_ids.update(
            contradiction.source_content_ids
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

    # ========================================================
    # REFERENCES
    # ========================================================

    for event in notebook.events:

        if not event.note_ids:

            raise ValueError(
                "Un événement ne possède aucune "
                "note documentaire : "
                f"{event.event_id}"
            )

        unknown_note_ids = (
            set(event.note_ids)
            - note_id_set
        )

        unknown_number_ids = (
            set(event.number_ids)
            - number_id_set
        )

        if unknown_note_ids:

            raise ValueError(
                "Un événement référence des notes "
                "inconnues"
            )

        if unknown_number_ids:

            raise ValueError(
                "Un événement référence des Numbers "
                "inconnus"
            )
    for section in notebook.sections:

        if not section.title:

            raise ValueError(
                "Une section possède un titre vide"
            )

        if (
            not section.event_ids
            and not section.note_ids
            and not section.number_ids
        ):

            raise ValueError(
                "Une section documentaire est vide"
            )

        if (
            set(section.event_ids)
            - event_id_set
        ):

            raise ValueError(
                "Une section référence des événements "
                "inconnus"
            )

        if (
            set(section.note_ids)
            - note_id_set
        ):

            raise ValueError(
                "Une section référence des notes "
                "inconnues"
            )

        if (
            set(section.number_ids)
            - number_id_set
        ):

            raise ValueError(
                "Une section référence des Numbers "
                "inconnus"
            )

    # ========================================================
    # PLACEMENT
    # ========================================================

    event_note_counts = _count_references([
        event.note_ids
        for event in notebook.events
    ])

    event_number_counts = _count_references([
        event.number_ids
        for event in notebook.events
    ])

    section_event_counts = _count_references([
        section.event_ids
        for section in notebook.sections
    ])

    section_note_counts = _count_references([
        section.note_ids
        for section in notebook.sections
    ])

    section_number_counts = _count_references([
        section.number_ids
        for section in notebook.sections
    ])

    invalid_events = [
        event_id
        for event_id in event_ids
        if section_event_counts.get(
            event_id,
            0,
        ) != 1
    ]

    invalid_notes = [
        note_id
        for note_id in note_ids
        if (
            event_note_counts.get(
                note_id,
                0,
            )
            + section_note_counts.get(
                note_id,
                0,
            )
        ) != 1
    ]

    invalid_numbers = [
        number_id
        for number_id in number_ids
        if (
            event_number_counts.get(
                number_id,
                0,
            )
            + section_number_counts.get(
                number_id,
                0,
            )
        ) != 1
    ]

    if invalid_events:

        raise ValueError(
            "Certains événements ne sont pas "
            "placés exactement une fois"
        )

    if invalid_notes:

        raise ValueError(
            "Certaines notes ne sont pas "
            "placées exactement une fois"
        )

    if invalid_numbers:

        raise ValueError(
            "Certains Numbers ne sont pas "
            "placés exactement une fois"
        )

    # ========================================================
    # TIMELINE AND CONTRADICTIONS
    # ========================================================

    for item in notebook.timeline:

        if (
            item.event_id
            and item.event_id
            not in event_id_set
        ):

            raise ValueError(
                "La timeline référence un événement "
                "inconnu"
            )

        if (
            set(item.note_ids)
            - note_id_set
        ):

            raise ValueError(
                "La timeline référence des notes "
                "inconnues"
            )

    for contradiction in notebook.contradictions:

        if (
            set(contradiction.note_ids)
            - note_id_set
        ):

            raise ValueError(
                "Une contradiction référence des "
                "notes inconnues"
            )


# ============================================================
# PREPARE NOTEBOOK
# ============================================================

def prepare_notebook(
    notebook: TouchCorpusNotebook,
    allowed_content_ids: set[str],
) -> TouchCorpusNotebook:

    normalized = normalize_notebook(
        notebook
    )

    repaired = repair_documentary_plan(
        normalized
    )

    validate_notebook(
        notebook=repaired,
        allowed_content_ids=(
            allowed_content_ids
        ),
    )

    return repaired
