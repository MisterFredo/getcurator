import json
import re
import unicodedata

from typing import (
    Any,
    Optional,
)

from pydantic import (
    BaseModel,
    Field,
)

from core.touch.notebook_models import (
    TouchCorpusNotebook,
    TouchEvidenceNote,
    TouchNotebookContradiction,
    TouchNotebookEvent,
    TouchNotebookNumber,
    TouchNotebookRequest,
    TouchNotebookSection,
    TouchNotebookTimelineItem,
)

from core.touch.notebook_organization_prompt import (
    TOUCH_NOTEBOOK_ORGANIZATION_SYSTEM_PROMPT,
    build_touch_notebook_organization_prompt,
)

from core.touch.notebook_plan_service import prepare_notebook

from core.touch.notebook_utils import (
    build_retry_prompt,
    extract_json_object,
    unique_ids,
)

from utils.llm import (
    run_llm_json,
)


# ============================================================
# ORGANIZATION RESULT
# ============================================================

class TouchNotebookOrganizationResult(
    BaseModel,
):

    corpus_summary: str = ""

    sections: list[
        TouchNotebookSection
    ] = Field(
        default_factory=list,
    )

    events: list[
        TouchNotebookEvent
    ] = Field(
        default_factory=list,
    )

    timeline: list[
        TouchNotebookTimelineItem
    ] = Field(
        default_factory=list,
    )

    contradictions: list[
        TouchNotebookContradiction
    ] = Field(
        default_factory=list,
    )

    corpus_strengths: list[str] = Field(
        default_factory=list,
    )

    corpus_limits: list[str] = Field(
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
# NORMALIZE OPTIONAL STRING
# ============================================================

def _normalize_optional_string(
    value: Any,
) -> str | None:

    if value is None:

        return None

    normalized_value = (
        str(
            value
        ).strip()
    )

    return (
        normalized_value
        if normalized_value
        else None
    )


# ============================================================
# NORMALIZE SECTION
# ============================================================

def _normalize_section(
    raw_section: Any,
    index: int,
) -> dict:

    if not isinstance(
        raw_section,
        dict,
    ):

        raise ValueError(
            "Une section du plan n’est pas "
            "un objet JSON"
        )

    return {

        "section_id":
            str(
                raw_section.get(
                    "section_id"
                )
                or f"section-{index + 1:03d}"
            ).strip(),

        "title":
            str(
                raw_section.get(
                    "title"
                )
                or ""
            ).strip(),

        "description":
            str(
                raw_section.get(
                    "description"
                )
                or ""
            ).strip(),

        "event_ids":
            _normalize_string_list(
                raw_section.get(
                    "event_ids"
                )
            ),

        "note_ids":
            _normalize_string_list(
                raw_section.get(
                    "note_ids"
                )
            ),

        # Certified Numbers are not organised
        # inside documentary sections.
        "number_ids":
            [],

    }


# ============================================================
# NORMALIZE EVENT
# ============================================================

def _normalize_event(
    raw_event: Any,
    index: int,
) -> dict:

    if not isinstance(
        raw_event,
        dict,
    ):

        raise ValueError(
            "Un événement du plan n’est pas "
            "un objet JSON"
        )

    return {

        "event_id":
            str(
                raw_event.get(
                    "event_id"
                )
                or f"event-{index + 1:03d}"
            ).strip(),

        "title":
            str(
                raw_event.get(
                    "title"
                )
                or ""
            ).strip(),

        "description":
            str(
                raw_event.get(
                    "description"
                )
                or ""
            ).strip(),

        "event_date":
            _normalize_optional_string(
                raw_event.get(
                    "event_date"
                )
            ),

        "actors":
            _normalize_string_list(
                raw_event.get(
                    "actors"
                )
            ),

        "note_ids":
            _normalize_string_list(
                raw_event.get(
                    "note_ids"
                )
            ),

        # Certified Numbers are not organised
        # inside documentary events.
        "number_ids":
            [],

        "source_content_ids":
            _normalize_string_list(
                raw_event.get(
                    "source_content_ids"
                )
            ),

    }


# ============================================================
# NORMALIZE TIMELINE ITEM
# ============================================================

def _normalize_timeline_item(
    raw_item: Any,
) -> dict:

    if not isinstance(
        raw_item,
        dict,
    ):

        raise ValueError(
            "Un élément de timeline n’est pas "
            "un objet JSON"
        )

    return {

        "date":
            str(
                raw_item.get(
                    "date"
                )
                or ""
            ).strip(),

        "label":
            str(
                raw_item.get(
                    "label"
                )
                or ""
            ).strip(),

        "description":
            str(
                raw_item.get(
                    "description"
                )
                or ""
            ).strip(),

        "event_id":
            _normalize_optional_string(
                raw_item.get(
                    "event_id"
                )
            ),

        "note_ids":
            _normalize_string_list(
                raw_item.get(
                    "note_ids"
                )
            ),

        "source_content_ids":
            _normalize_string_list(
                raw_item.get(
                    "source_content_ids"
                )
            ),

    }


# ============================================================
# NORMALIZE CONTRADICTION
# ============================================================

def _normalize_contradiction(
    raw_contradiction: Any,
) -> dict:

    if not isinstance(
        raw_contradiction,
        dict,
    ):

        raise ValueError(
            "Une contradiction n’est pas "
            "un objet JSON"
        )

    return {

        "subject":
            str(
                raw_contradiction.get(
                    "subject"
                )
                or ""
            ).strip(),

        "description":
            str(
                raw_contradiction.get(
                    "description"
                )
                or ""
            ).strip(),

        "note_ids":
            _normalize_string_list(
                raw_contradiction.get(
                    "note_ids"
                )
            ),

        "source_content_ids":
            _normalize_string_list(
                raw_contradiction.get(
                    "source_content_ids"
                )
            ),

        "resolution":
            _normalize_optional_string(
                raw_contradiction.get(
                    "resolution"
                )
            ),

    }


# ============================================================
# NORMALIZE PAYLOAD
# ============================================================

def _normalize_organization_payload(
    parsed: dict,
) -> dict:

    raw_sections = (
        parsed.get(
            "sections",
            [],
        )
        or []
    )

    raw_events = (
        parsed.get(
            "events",
            [],
        )
        or []
    )

    raw_timeline = (
        parsed.get(
            "timeline",
            [],
        )
        or []
    )

    raw_contradictions = (
        parsed.get(
            "contradictions",
            [],
        )
        or []
    )

    if not isinstance(
        raw_sections,
        list,
    ):

        raw_sections = []

    if not isinstance(
        raw_events,
        list,
    ):

        raw_events = []

    if not isinstance(
        raw_timeline,
        list,
    ):

        raw_timeline = []

    if not isinstance(
        raw_contradictions,
        list,
    ):

        raw_contradictions = []

    return {

        "corpus_summary":
            str(
                parsed.get(
                    "corpus_summary"
                )
                or ""
            ).strip(),

        "sections": [

            _normalize_section(
                raw_section=raw_section,
                index=index,
            )

            for index, raw_section
            in enumerate(
                raw_sections
            )

        ],

        "events": [

            _normalize_event(
                raw_event=raw_event,
                index=index,
            )

            for index, raw_event
            in enumerate(
                raw_events
            )

        ],

        "timeline": [

            _normalize_timeline_item(
                raw_item
            )

            for raw_item
            in raw_timeline

        ],

        "contradictions": [

            _normalize_contradiction(
                raw_contradiction
            )

            for raw_contradiction
            in raw_contradictions

        ],

        "corpus_strengths":
            _normalize_string_list(
                parsed.get(
                    "corpus_strengths"
                )
            ),

        "corpus_limits":
            _normalize_string_list(
                parsed.get(
                    "corpus_limits"
                )
            ),

    }

# ============================================================
# NORMALIZE COMPARATIVE LABEL
# ============================================================

def _normalize_comparative_label(
    value: str,
) -> str:

    normalized = unicodedata.normalize(
        "NFKD",
        value or "",
    )

    normalized = "".join(

        character

        for character in normalized

        if not unicodedata.combining(
            character
        )

    )

    normalized = normalized.lower()

    normalized = re.sub(
        r"[^a-z0-9]+",
        " ",
        normalized,
    )

    return " ".join(
        normalized.split()
    )


# ============================================================
# GET COMPARATIVE SUBJECT MARKERS
# ============================================================

def _get_comparative_subject_markers(
    request: TouchNotebookRequest,
) -> list[str]:

    markers: list[str] = []

    for axis in request.report_design.axes:

        if axis.axis_type != "CORE_SUBJECT":

            continue

        candidate = ""

        if axis.search_terms:

            candidate = (
                axis.search_terms[0]
            )

        if not candidate:

            candidate = axis.label

        normalized_candidate = (
            _normalize_comparative_label(
                candidate
            )
        )

        if (
            normalized_candidate
            and normalized_candidate
            not in markers
        ):

            markers.append(
                normalized_candidate
            )

    return markers


# ============================================================
# VALIDATE COMPARATIVE ORGANIZATION
# ============================================================

def _validate_comparative_organization(
    request: TouchNotebookRequest,
    organization:
        TouchNotebookOrganizationResult,
) -> None:

    if (
        request
        .report_design
        .report_archetype
        != "COMPARATIVE_ANALYSIS"
    ):

        return

    if len(
        organization.sections
    ) < 2:

        raise ValueError(
            "COMPARATIVE_STRUCTURE_INVALID: "
            "A comparative report requires several "
            "shared analytical dimensions."
        )

    subject_markers = (
        _get_comparative_subject_markers(
            request
        )
    )

    if len(subject_markers) < 2:

        return

    actor_specific_sections: list[str] = []

    generic_comparison_sections: list[str] = []

    for section in organization.sections:

        normalized_title = (
            _normalize_comparative_label(
                section.title
            )
        )

        matched_markers = [

            marker

            for marker in subject_markers

            if marker in normalized_title

        ]

        # A section naming only one compared subject is
        # an actor profile, not a comparative dimension.
        if len(matched_markers) == 1:

            actor_specific_sections.append(
                section.title
            )

        title_words = (
            normalized_title.split()
        )

        if (
            title_words
            and title_words[0]
            in {
                "comparison",
                "comparaison",
                "comparative",
                "comparatif",
            }
            and len(title_words) <= 5
        ):

            generic_comparison_sections.append(
                section.title
            )

    if actor_specific_sections:

        raise ValueError(
            "COMPARATIVE_STRUCTURE_INVALID: "
            "The documentary plan contains sections "
            "organized around only one compared subject: "
            + ", ".join(
                actor_specific_sections
            )
            + ". Rebuild the entire plan around shared "
            "analytical dimensions. Each section must "
            "compare the supplied subjects on one common "
            "dimension, or explicitly document an evidence "
            "imbalance. Do not create separate subject "
            "profiles."
        )

    if generic_comparison_sections:

        raise ValueError(
            "COMPARATIVE_STRUCTURE_INVALID: "
            "The documentary plan contains a generic "
            "comparison section: "
            + ", ".join(
                generic_comparison_sections
            )
            + ". Comparison must structure the whole "
            "notebook through shared dimensions, not be "
            "isolated in one final section."
        )


# ============================================================
# REVIEW CONCENTRATED DOCUMENTARY PLANS
# ============================================================

def _review_concentrated_plan(
    request: TouchNotebookRequest,
    notebook: TouchCorpusNotebook,
    model: Optional[str],
) -> None:
    """Volume triggers a semantic review, never a compulsory split."""
    if request.report_design.organization_mode == "CHRONOLOGICAL":
        return

    note_by_id = {note.note_id: note for note in notebook.notes}
    event_by_id = {event.event_id: event for event in notebook.events}
    placements = []
    for section in notebook.sections:
        ids = set(section.note_ids)
        for event_id in section.event_ids:
            ids.update(event_by_id[event_id].note_ids)
        placements.append({
            "title": section.title,
            "note_ids": sorted(ids),
            "events": [event_by_id[event_id].model_dump(mode="json")
                       for event_id in section.event_ids],
        })

    source_ids = {source_id for note in notebook.notes
                  for source_id in note.source_content_ids}
    largest = max((len(item["note_ids"]) for item in placements), default=0)
    # Conservative diagnostic thresholds; they do not measure semantic diversity.
    suspicious = (len(note_by_id) >= 30 and len(source_ids) >= 6
                  and largest / max(len(note_by_id), 1) >= 0.85)
    if not suspicious:
        return

    payload = {
        "subject": request.subject,
        "objective": request.objective,
        "report_design": request.report_design.model_dump(mode="json"),
        "sections": placements,
        "notes": [note.model_dump(mode="json") for note in notebook.notes],
    }
    review = extract_json_object(run_llm_json(
        prompt=(
            "Review this documentary plan using only the supplied evidence. "
            "Decide whether the large section combines distinct, sufficiently "
            "documented functions that need separate navigation. A homogeneous "
            "corpus may legitimately have one section regardless of volume. "
            "Do not impose a section count, invent themes or force unsupported "
            "research axes. For chronological organization, preserve chronology. "
            "Return JSON with exactly: acceptable (boolean), reason (string). "
            "If unacceptable, identify the distinct mechanisms and cite supplied "
            "note_ids demonstrating the problem. Do not rewrite notes.\n"
            + json.dumps(payload, ensure_ascii=False)
        ),
        model=model,
        temperature=0.0,
        system_prompt="You review evidence-based documentary organization. Return JSON only.",
    ))
    if (type(review.get("acceptable")) is not bool
            or not isinstance(review.get("reason"), str)
            or not review["reason"].strip()):
        raise ValueError("DOCUMENTARY_REVIEW_INVALID: missing boolean verdict or reason.")
    print("TOUCH_NOTEBOOK_STRUCTURE_REVIEW", {
        "acceptable": review["acceptable"], "reason": review["reason"],
        "sections_count": len(notebook.sections), "notes_count": len(note_by_id),
    })
    if not review["acceptable"]:
        raise ValueError(
            "DOCUMENTARY_STRUCTURE_INVALID: " + review["reason"]
            + " Rebuild the plan around the distinct documented functions. "
            "Preserve relevant evidence and immutable note identifiers."
        )


def _validate_documentary_note_coverage(
    notes: list[TouchEvidenceNote],
    notebook: TouchCorpusNotebook,
) -> None:
    """Organization must place extracted evidence, not silently reselect it."""
    expected_ids = {note.note_id for note in notes}
    event_by_id = {event.event_id: event for event in notebook.events}
    placed_ids: set[str] = set()
    for section in notebook.sections:
        placed_ids.update(section.note_ids)
        for event_id in section.event_ids:
            event = event_by_id.get(event_id)
            if event is not None:
                placed_ids.update(event.note_ids)
    missing_ids = sorted(expected_ids - placed_ids)
    retained_ids = {note.note_id for note in notebook.notes}
    removed_ids = sorted(expected_ids - retained_ids)
    if missing_ids or removed_ids:
        raise ValueError(
            "DOCUMENTARY_COVERAGE_INVALID: "
            f"{len(expected_ids & placed_ids)}/{len(expected_ids)} supplied notes "
            "are placed in sections or their referenced events. "
            "All supplied evidence notes must remain available and navigable. "
            "Missing placements: " + json.dumps(missing_ids)
            + ". Removed notes: " + json.dumps(removed_ids)
            + ". Restore these exact note_ids from the original evidence and "
            "distribute them across the appropriate documented mechanisms. "
            "Diagnostic example note_ids are examples, not a selected subset. "
            "Group complementary or repeated evidence into events without "
            "discarding its note references. Do not add a catch-all section "
            "merely to satisfy coverage."
        )


def _build_organization_repair_prompt(
    original_prompt: str,
    error: str,
    rejected_payload: Optional[dict[str, Any]],
) -> str:
    """Give the retry the actual rejected plan, not only its diagnosis."""
    if rejected_payload is None:
        return build_retry_prompt(original_prompt=original_prompt, error=error)

    structural = error.startswith("DOCUMENTARY_STRUCTURE_INVALID:")
    instruction = (
        "Reconstruct the documentary sections around the distinct functions "
        "identified in the diagnosis, where supported by the supplied notes. "
        "Do not return the same grouping with cosmetic title changes. "
        "Redistribute the relevant note_ids and event_ids into navigable sections. "
        "Keep complementary evidence about the same event together. "
        "If an event incorrectly combines distinct mechanisms, rebuild its "
        "grouping from the original notes. Do not invent evidence or new note_ids. "
        "Do not discard notes to avoid the structural review. "
        "No fixed section count is required."
        if structural else
        "Correct the rejected organization using the diagnosis and the original "
        "schema. Preserve evidence and immutable note identifiers."
    )
    return (
        "REPAIR A REJECTED DOCUMENTARY ORGANIZATION\n"
        "The previous organization was rejected. Produce a corrected complete "
        "JSON object, not an explanation or a patch.\n\n"
        "VALIDATION DIAGNOSIS\n" + error + "\n\n"
        "REPAIR REQUIREMENTS\n" + instruction + "\n\n"
        "REJECTED ORGANIZATION (reference only; it is not a valid template)\n"
        + json.dumps(rejected_payload, ensure_ascii=False, indent=2)
        + "\n\nORIGINAL TASK, EVIDENCE AND REQUIRED SCHEMA\n"
        + original_prompt
        + "\n\nFINAL CHECK\nResolve the diagnosis above before returning the "
        "complete JSON organization. Use only the original supplied evidence."
    )


# ============================================================
# BUILD NOTEBOOK
# ============================================================

def _build_notebook(
    request: TouchNotebookRequest,
    organization:
        TouchNotebookOrganizationResult,
    notes: list[
        TouchEvidenceNote
    ],
    certified_numbers: list[
        TouchNotebookNumber
    ],
) -> TouchCorpusNotebook:

    return TouchCorpusNotebook(

        subject=(
            request.subject.strip()
        ),

        objective=(
            request.objective.strip()
        ),

        corpus_summary=(
            organization
            .corpus_summary
            .strip()
        ),

        sections=(
            organization.sections
        ),

        notes=notes,

        events=(
            organization.events
        ),

        timeline=(
            organization.timeline
        ),

        dimensions=[],

        # Certified Numbers remain complete and unchanged,
        # but are not part of the documentary plan.
        validated_numbers=(
            certified_numbers
        ),

        quarantined_numbers=[],

        contradictions=(
            organization.contradictions
        ),

        corpus_strengths=(
            organization.corpus_strengths
        ),

        corpus_limits=(
            organization.corpus_limits
        ),

    )


# ============================================================
# ORGANIZE NOTEBOOK
# ============================================================

def organize_notebook(
    request: TouchNotebookRequest,
    notes: list[
        TouchEvidenceNote
    ],
    certified_numbers: list[
        TouchNotebookNumber
    ],
    model: Optional[str] = None,
    max_attempts: int = 2,
) -> TouchCorpusNotebook:

    # The documentary plan is built exclusively
    # from qualitative contribution notes.
    if not notes:

        raise ValueError(
            "Aucune note documentaire "
            "à organiser"
        )

    original_prompt = (
        build_touch_notebook_organization_prompt(

            request=request,

            notes=notes,

        )
    )

    original_prompt += (
        "\n\nEVIDENCE PRESERVATION REQUIREMENT\n"
        "This stage organizes the supplied evidence; it does not select a small "
        "summary subset. Every supplied note_id must be reachable from a "
        "section.note_ids or from the note_ids of an event referenced by a "
        "section.event_ids. Standalone unreferenced events do not count. "
        "Group complementary or repeated evidence without losing note references. "
        "Do not invent a generic remainder section. "
        "When repairing a plan, diagnostic note_ids are illustrative examples, "
        "not an exhaustive list of the notes to retain.\n"
        "REQUIRED NOTE IDS\n"
        + json.dumps([note.note_id for note in notes], ensure_ascii=False)
    )

    prompt = original_prompt

    attempts = max(
        1,
        max_attempts,
    )

    last_error = (
        "Erreur inconnue pendant "
        "l’organisation du notebook"
    )

    for attempt in range(
        attempts
    ):

        rejected_payload: Optional[dict[str, Any]] = None

        try:

            raw_content = run_llm_json(

                prompt=prompt,

                model=model,

                temperature=0.0,

                system_prompt=(
                    TOUCH_NOTEBOOK_ORGANIZATION_SYSTEM_PROMPT
                ),

            )

            parsed = extract_json_object(
                raw_content
            )

            normalized_payload = (
                _normalize_organization_payload(
                    parsed
                )
            )

            rejected_payload = normalized_payload

            organization = (
                TouchNotebookOrganizationResult
                .model_validate(
                    normalized_payload
                )
            )
            
            _validate_comparative_organization(
                request=request,
                organization=organization,
            )
            
            notebook = _build_notebook(

                request=request,

                organization=(
                    organization
                ),

                notes=notes,

                certified_numbers=(
                    certified_numbers
                ),

            )

            print("TOUCH_NOTEBOOK_ORGANIZATION_RAW", {
                "attempt": attempt + 1,
                "sections": [{"title": section.title,
                              "direct_notes": len(section.note_ids),
                              "events": len(section.event_ids)}
                             for section in notebook.sections],
                "events_count": len(notebook.events),
                "notes_count": len(notebook.notes),
            })
            _validate_documentary_note_coverage(notes, notebook)
            notebook = prepare_notebook(
                notebook=notebook,
                allowed_content_ids=set(request.content_ids),
            )
            _validate_documentary_note_coverage(notes, notebook)
            # Review the effective plan, after empty sections and invalid
            # references have been repaired. Structural errors also retry here.
            _validate_comparative_organization(
                request=request,
                organization=TouchNotebookOrganizationResult(
                    sections=notebook.sections,
                ),
            )
            # Send the effective rejected plan back to the organizer, including
            # any repairs already performed by prepare_notebook.
            rejected_payload = dict(normalized_payload)
            rejected_payload["sections"] = [
                section.model_dump(mode="json") for section in notebook.sections
            ]
            rejected_payload["events"] = [
                event.model_dump(mode="json") for event in notebook.events
            ]
            _review_concentrated_plan(request, notebook, model)
            print("TOUCH_NOTEBOOK_ORGANIZATION_ACCEPTED", {
                "attempt": attempt + 1,
                "sections_count": len(notebook.sections),
                "events_count": len(notebook.events),
                "notes_count": len(notebook.notes),
            })
            return notebook

        except Exception as exc:

            last_error = str(
                exc
            )

            print("TOUCH_NOTEBOOK_ORGANIZATION_RETRY", {
                "attempt": attempt + 1, "error": last_error,
                "will_retry": attempt + 1 < attempts,
            })

            if (
                attempt + 1
                >= attempts
            ):

                break

            prompt = _build_organization_repair_prompt(
                original_prompt=original_prompt,
                error=last_error,
                rejected_payload=rejected_payload,
            )

    raise ValueError(
        "Échec de l’organisation du notebook "
        f"après {attempts} tentative(s) : "
        f"{last_error}"
    )
