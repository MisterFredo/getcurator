from datetime import datetime

from core.touch.notebook_models import (
    TouchCorpusNotebook,
    TouchNotebookSection,
)
from core.touch.notebook_utils import unique_ids


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
                        note.explanation
                        or ""
                    ).strip(),

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
                        event.description
                        or ""
                    ).strip(),

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

                # Structured Numbers are not part of
                # the documentary plan.
                "number_ids":
                    [],

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
                        section.description
                        or ""
                    ).strip(),

                "event_ids":
                    unique_ids(
                        section.event_ids
                    ),

                "note_ids":
                    unique_ids(
                        section.note_ids
                    ),

                # Structured Numbers are not part of
                # the documentary plan.
                "number_ids":
                    [],

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
                        item.description
                        or ""
                    ).strip(),

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

        for contradiction
        in notebook.contradictions

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

            # Deprecated presentation layer.
            "dimensions":
                [],

            # Complete canonical Numbers registry.
            "validated_numbers":
                validated_numbers,

            # Rejected Numbers remain inside the
            # dedicated Numbers workflow.
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

    normalized = (
        value
        or ""
    ).strip()

    for date_format in (
        "%Y-%m-%d",
        "%Y-%m",
        "%Y",
    ):

        try:

            return (
                0,
                datetime.strptime(
                    normalized,
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

def _event_sources(
    event,
    notes_by_id: dict,
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

    return source_ids


# ============================================================
# SECTION SOURCES
# ============================================================

def _section_sources(
    section,
    events_by_id: dict,
    notes_by_id: dict,
) -> set[str]:

    source_ids: set[str] = set()

    for event_id in section.event_ids:

        event = events_by_id.get(
            event_id
        )

        if event:

            source_ids.update(
                _event_sources(
                    event,
                    notes_by_id,
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
) -> int | None:

    if not item_source_ids:

        return None

    best_index = None
    best_score = 0

    for index, section in enumerate(
        sections
    ):

        section_source_ids = (
            _section_sources(
                section,
                events_by_id,
                notes_by_id,
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

    values = list(
        getattr(
            section,
            field_name,
        )
    )

    values.append(
        item_id
    )

    sections[
        section_index
    ] = section.model_copy(
        update={
            field_name:
                unique_ids(
                    values
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

    valid_note_ids = set(
        notes_by_id
    )

    # ========================================================
    # EVENTS
    # ========================================================

    repaired_events = []

    used_event_note_ids: set[str] = set()

    for event in notebook.events:

        note_ids = [

            note_id

            for note_id in event.note_ids

            if (
                note_id
                in valid_note_ids

                and note_id
                not in used_event_note_ids
            )

        ]

        # An event without any documentary note
        # does not belong in the notebook plan.
        if not note_ids:

            continue

        used_event_note_ids.update(
            note_ids
        )

        repaired_events.append(

            event.model_copy(
                update={

                    "note_ids":
                        note_ids,

                    "number_ids":
                        [],

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

    for section in notebook.sections:

        event_ids = [

            event_id

            for event_id
            in section.event_ids

            if (
                event_id
                in valid_event_ids

                and event_id
                not in used_section_event_ids
            )

        ]

        note_ids = [

            note_id

            for note_id
            in section.note_ids

            if (
                note_id
                in valid_note_ids

                and note_id
                not in used_event_note_ids

                and note_id
                not in used_section_note_ids
            )

        ]

        if (
            not event_ids
            and not note_ids
        ):

            continue

        used_section_event_ids.update(
            event_ids
        )

        used_section_note_ids.update(
            note_ids
        )

        repaired_sections.append(

            section.model_copy(
                update={

                    "event_ids":
                        event_ids,

                    "note_ids":
                        note_ids,

                    "number_ids":
                        [],

                },
            )

        )

    # ========================================================
    # UNRESOLVED EVENTS
    # ========================================================

    unresolved_event_ids = []

    for event in repaired_events:

        if (
            event.event_id
            in used_section_event_ids
        ):

            continue

        section_index = (
            _find_best_section_index(

                _event_sources(
                    event,
                    notes_by_id,
                ),

                repaired_sections,

                events_by_id,

                notes_by_id,

            )
        )

        if section_index is None:

            unresolved_event_ids.append(
                event.event_id
            )

        else:

            _attach_item_to_section(

                repaired_sections,

                section_index,

                "event_ids",

                event.event_id,

            )

    # ========================================================
    # UNRESOLVED NOTES
    # ========================================================

    unresolved_note_ids = []

    for note in notebook.notes:

        if (
            note.note_id
            in used_event_note_ids

            or note.note_id
            in used_section_note_ids
        ):

            continue

        section_index = (
            _find_best_section_index(

                set(
                    note.source_content_ids
                ),

                repaired_sections,

                events_by_id,

                notes_by_id,

            )
        )

        if section_index is None:

            unresolved_note_ids.append(
                note.note_id
            )

        else:

            _attach_item_to_section(

                repaired_sections,

                section_index,

                "note_ids",

                note.note_id,

            )

    # ========================================================
    # FINAL DOCUMENTARY REGISTRY
    # ========================================================
    
    # Items that could not be attached to a meaningful section
    # are excluded from the final notebook instead of being
    # placed in a generic catch-all section.
    
    placed_event_ids = {
    
        event_id
    
        for section in repaired_sections
    
        for event_id in section.event_ids
    
    }
    
    final_events = [
    
        event
    
        for event in repaired_events
    
        if event.event_id in placed_event_ids
    
    ]
    
    final_events_by_id = {
    
        event.event_id:
            event
    
        for event in final_events
    
    }
    
    placed_note_ids = {
    
        note_id
    
        for section in repaired_sections
    
        for note_id in section.note_ids
    
    }
    
    for event in final_events:
    
        placed_note_ids.update(
            event.note_ids
        )
    
    final_notes = [
    
        note
    
        for note in notebook.notes
    
        if note.note_id in placed_note_ids
    
    ]
    
    final_note_ids = set(
        placed_note_ids
    )
    
    final_event_ids = set(
        placed_event_ids
    )

    # ========================================================
    # TIMELINE
    # ========================================================
    
    repaired_timeline = []
    
    for item in notebook.timeline:
    
        if not item.date:
    
            continue
    
        valid_item_event_id = (
    
            item.event_id
    
            if (
                item.event_id
                and item.event_id
                in final_event_ids
            )
    
            else None
    
        )
    
        valid_item_note_ids = [
    
            note_id
    
            for note_id in item.note_ids
    
            if note_id in final_note_ids
    
        ]
    
        if (
            valid_item_event_id is None
            and not valid_item_note_ids
        ):
    
            continue
    
        timeline_source_ids: set[str] = set()
    
        if valid_item_event_id:
    
            timeline_event = (
                final_events_by_id[
                    valid_item_event_id
                ]
            )
    
            timeline_source_ids.update(
    
                _event_sources(
                    timeline_event,
                    notes_by_id,
                )
    
            )
    
        for note_id in valid_item_note_ids:
    
            timeline_source_ids.update(
    
                notes_by_id[
                    note_id
                ].source_content_ids
    
            )
    
        repaired_timeline.append(
    
            item.model_copy(
                update={
    
                    "event_id":
                        valid_item_event_id,
    
                    "note_ids":
                        valid_item_note_ids,
    
                    "source_content_ids":
                        unique_ids(
                            list(
                                timeline_source_ids
                            )
                        ),
    
                },
            )
    
        )
    
    
    repaired_timeline.sort(
        key=lambda item:
            _timeline_sort_key(
                item.date
            )
    )

    # ========================================================
    # CONTRADICTIONS
    # ========================================================
    
    repaired_contradictions = []
    
    for contradiction in notebook.contradictions:
    
        contradiction_note_ids = [
    
            note_id
    
            for note_id
            in contradiction.note_ids
    
            if note_id in final_note_ids
    
        ]
    
        if not contradiction_note_ids:
    
            continue
    
        contradiction_source_ids = unique_ids([
    
            content_id
    
            for note_id
            in contradiction_note_ids
    
            for content_id
            in notes_by_id[
                note_id
            ].source_content_ids
    
        ])
    
        repaired_contradictions.append(
    
            contradiction.model_copy(
                update={
    
                    "note_ids":
                        contradiction_note_ids,
    
                    "source_content_ids":
                        contradiction_source_ids,
    
                },
            )
    
        )

    return notebook.model_copy(
        update={

            "sections":
                repaired_sections,

            "notes":
                final_notes,

            "events":
                final_events,

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

    if (
        len(values)
        != len(
            set(
                values
            )
        )
    ):

        raise ValueError(
            "Le notebook contient des "
            f"{label} dupliqués"
        )

    if any(
        not value
        for value in values
    ):

        raise ValueError(
            "Le notebook contient un "
            f"{label} vide"
        )


# ============================================================
# COUNT REFERENCES
# ============================================================

def _count_references(
    references: list[
        list[str]
    ],
) -> dict[str, int]:

    counts: dict[str, int] = {}

    for group in references:

        for identifier in group:

            counts[
                identifier
            ] = (
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

        for section
        in notebook.sections

    ]

    note_ids = [

        note.note_id

        for note
        in notebook.notes

    ]

    event_ids = [

        event.event_id

        for event
        in notebook.events

    ]

    number_ids = [

        number.number_id

        for number
        in notebook.validated_numbers

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

    if not notebook.sections:

        raise ValueError(
            "Le notebook ne contient aucune "
            "section documentaire"
        )

    note_id_set = set(
        note_ids
    )

    event_id_set = set(
        event_ids
    )

    referenced_source_ids: set[str] = set()

    # ========================================================
    # NOTES
    # ========================================================

    for note in notebook.notes:

        if not note.source_content_ids:

            raise ValueError(
                "Une note ne possède aucune source : "
                f"{note.note_id}"
            )

        unknown_sources = (

            set(
                note.source_content_ids
            )

            - allowed_content_ids

        )

        if unknown_sources:

            raise ValueError(
                "Une note référence des contenus "
                "extérieurs au corpus : "
                f"{note.note_id} · "
                + ", ".join(
                    sorted(
                        unknown_sources
                    )
                )
            )

        referenced_source_ids.update(
            note.source_content_ids
        )

    # ========================================================
    # CERTIFIED NUMBERS
    # ========================================================

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

        unknown_sources = (

            set(
                number.source_content_ids
            )

            - allowed_content_ids

        )

        if unknown_sources:

            raise ValueError(
                "Un Number référence des sources "
                "extérieures au corpus : "
                f"{number.number_id} · "
                + ", ".join(
                    sorted(
                        unknown_sources
                    )
                )
            )

        referenced_source_ids.update(
            number.source_content_ids
        )

    # ========================================================
    # OTHER SOURCE REFERENCES
    # ========================================================

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

    unknown_sources = (

        referenced_source_ids
        - allowed_content_ids

    )

    if unknown_sources:

        raise ValueError(
            "Le notebook référence des sources "
            "inconnues : "
            + ", ".join(
                sorted(
                    unknown_sources
                )
            )
        )

    # ========================================================
    # EVENTS
    # ========================================================

    for event in notebook.events:

        if not event.note_ids:

            raise ValueError(
                "Un événement ne possède aucune "
                "note documentaire : "
                f"{event.event_id}"
            )

        unknown_notes = (

            set(
                event.note_ids
            )

            - note_id_set

        )

        if unknown_notes:

            raise ValueError(
                "Un événement référence des notes "
                "inconnues : "
                f"{event.event_id} · "
                + ", ".join(
                    sorted(
                        unknown_notes
                    )
                )
            )

        if event.number_ids:

            raise ValueError(
                "Un événement contient encore des "
                "number_ids : "
                f"{event.event_id}"
            )

    # ========================================================
    # SECTIONS
    # ========================================================

    for section in notebook.sections:

        if not section.title:

            raise ValueError(
                "Une section possède un titre vide"
            )

        if (
            not section.event_ids
            and not section.note_ids
        ):

            raise ValueError(
                "Une section documentaire est vide : "
                f"{section.section_id}"
            )

        unknown_events = (

            set(
                section.event_ids
            )

            - event_id_set

        )

        if unknown_events:

            raise ValueError(
                "Une section référence des événements "
                "inconnus : "
                f"{section.section_id} · "
                + ", ".join(
                    sorted(
                        unknown_events
                    )
                )
            )

        unknown_notes = (

            set(
                section.note_ids
            )

            - note_id_set

        )

        if unknown_notes:

            raise ValueError(
                "Une section référence des notes "
                "inconnues : "
                f"{section.section_id} · "
                + ", ".join(
                    sorted(
                        unknown_notes
                    )
                )
            )

        if section.number_ids:

            raise ValueError(
                "Une section contient encore des "
                "number_ids : "
                f"{section.section_id}"
            )

    # ========================================================
    # PLACEMENT
    # ========================================================

    event_note_counts = (
        _count_references([

            event.note_ids

            for event
            in notebook.events

        ])
    )

    section_event_counts = (
        _count_references([

            section.event_ids

            for section
            in notebook.sections

        ])
    )

    section_note_counts = (
        _count_references([

            section.note_ids

            for section
            in notebook.sections

        ])
    )

    invalid_events = [

        event_id

        for event_id in event_ids

        if (
            section_event_counts.get(
                event_id,
                0,
            )
            != 1
        )

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

            != 1

        )

    ]

    if invalid_events:

        raise ValueError(
            "Certains événements ne sont pas "
            "placés exactement une fois : "
            + ", ".join(
                sorted(
                    invalid_events
                )
            )
        )

    if invalid_notes:

        raise ValueError(
            "Certaines notes ne sont pas "
            "placées exactement une fois : "
            + ", ".join(
                sorted(
                    invalid_notes
                )
            )
        )

    # ========================================================
    # TIMELINE
    # ========================================================

    for item in notebook.timeline:

        if (
            item.event_id
            and item.event_id
            not in event_id_set
        ):

            raise ValueError(
                "La timeline référence un événement "
                "inconnu : "
                f"{item.event_id}"
            )

        unknown_notes = (

            set(
                item.note_ids
            )

            - note_id_set

        )

        if unknown_notes:

            raise ValueError(
                "La timeline référence des notes "
                "inconnues : "
                + ", ".join(
                    sorted(
                        unknown_notes
                    )
                )
            )

    # ========================================================
    # CONTRADICTIONS
    # ========================================================

    for contradiction in notebook.contradictions:

        unknown_notes = (

            set(
                contradiction.note_ids
            )

            - note_id_set

        )

        if unknown_notes:

            raise ValueError(
                "Une contradiction référence des "
                "notes inconnues : "
                + ", ".join(
                    sorted(
                        unknown_notes
                    )
                )
            )

def validate_executive_summary(
    notebook: TouchCorpusNotebook,
    allowed_content_ids: set[str],
) -> None:

    notes_by_id = {
        note.note_id: note
        for note in notebook.notes
    }

    summary_ids = [
        item.summary_id
        for item in notebook.executive_summary
    ]

    _validate_unique_identifiers(
        summary_ids,
        "summary_id",
    )

    for item in notebook.executive_summary:

        if not item.statement.strip():
            raise ValueError(
                "Un élément de l’Executive Summary "
                "possède un texte vide"
            )

        if not item.note_ids:
            raise ValueError(
                "Un élément de l’Executive Summary "
                "ne référence aucune note : "
                f"{item.summary_id}"
            )

        if len(item.note_ids) != len(set(item.note_ids)):
            raise ValueError(
                "Un élément de l’Executive Summary "
                "référence deux fois la même note : "
                f"{item.summary_id}"
            )

        unknown_note_ids = (
            set(item.note_ids)
            - set(notes_by_id)
        )

        if unknown_note_ids:
            raise ValueError(
                "L’Executive Summary référence des "
                "notes inconnues : "
                + ", ".join(sorted(unknown_note_ids))
            )

        expected_source_ids = {
            content_id
            for note_id in item.note_ids
            for content_id in notes_by_id[
                note_id
            ].source_content_ids
        }

        if (
            set(item.source_content_ids)
            != expected_source_ids
        ):
            raise ValueError(
                "Les sources de l’Executive Summary "
                "ne correspondent pas aux notes : "
                f"{item.summary_id}"
            )

        if (
            expected_source_ids
            - allowed_content_ids
        ):
            raise ValueError(
                "L’Executive Summary référence des "
                "sources hors du corpus : "
                f"{item.summary_id}"
            )


# ============================================================
# PREPARE NOTEBOOK
# ============================================================

def prepare_notebook(
    notebook: TouchCorpusNotebook,
    allowed_content_ids: set[str],
) -> TouchCorpusNotebook:

    normalized = (
        normalize_notebook(
            notebook
        )
    )

    repaired = (
        repair_documentary_plan(
            normalized
        )
    )

    validate_notebook(
        repaired,
        allowed_content_ids,
    )

    return repaired
