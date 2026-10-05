import json
import logging
import os
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

from core.touch.notebook_assignment_prompt import (
    TOUCH_NOTEBOOK_ASSIGNMENT_SYSTEM_PROMPT,
    TOUCH_NOTEBOOK_ASSESSMENT_SYSTEM_PROMPT,
    build_touch_notebook_assignment_prompt,
)

from core.touch.notebook_outline_prompt import (
    TOUCH_NOTEBOOK_OUTLINE_SYSTEM_PROMPT,
    build_touch_notebook_outline_prompt,
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
# REVIEW SINGLE-SECTION NAVIGATION
# ============================================================

def _normalize_unattached_events(organization):
    """Remove orphan event wrappers, never the evidence they reference.

    Already placed notes keep their primary section. Unplaced notes remain
    in the input registry and trigger the normal coverage repair with exact IDs.
    Timeline references to an orphan event become references to its notes.
    """
    attached = {event_id for section in organization.sections
                for event_id in section.event_ids}
    orphan_events = {event.event_id: event for event in organization.events
                     if event.event_id not in attached}
    if not orphan_events:
        return organization
    timeline = []
    for item in organization.timeline:
        orphan = orphan_events.get(item.event_id)
        if orphan is None:
            timeline.append(item)
        else:
            timeline.append(item.model_copy(update={
                "event_id": None,
                "note_ids": unique_ids(list(item.note_ids) + list(orphan.note_ids)),
            }))
    logger.warning(
        "TOUCH_NOTEBOOK_ORPHAN_EVENTS event_notes=%s",
        {event_id: list(event.note_ids) for event_id, event in orphan_events.items()},
    )
    return organization.model_copy(update={
        "events": [event for event in organization.events
                   if event.event_id not in orphan_events],
        "timeline": timeline,
    })


def _repair_remaining_note_assignments(request, organization, notes, exclusions, model):
    """One bounded repair call for missing assignments, without rebuilding the plan."""
    placed = {note_id for section in organization.sections for note_id in section.note_ids}
    for event in organization.events:
        placed.update(event.note_ids)
    excluded_ids = {item.get("note_id") for item in exclusions if isinstance(item, dict)}
    missing = [note for note in notes if note.note_id not in placed | excluded_ids]
    if not missing:
        return organization, exclusions
    section_ids = {section.section_id for section in organization.sections}
    payload = {
        "subject": request.subject,
        "objective": request.objective,
        "output_language": request.output_language,
        "report_design": request.report_design.model_dump(mode="json"),
        "current_plan": organization.model_dump(mode="json"),
        "existing_notes": [note.model_dump(mode="json") for note in notes
                           if note.note_id in placed],
        "unassigned_notes": [note.model_dump(mode="json") for note in missing],
    }
    raw = run_llm_json(
        prompt="Assign only the unassigned notes. Return the required JSON.\n"
               + json.dumps(payload, ensure_ascii=False),
        model=model,
        temperature=0.0,
        system_prompt=(
            "You repair missing assignments in a documentary notebook. "
            "Do not regenerate the existing plan, notes or events. For each "
            "unassigned note, choose the appropriate existing section by its "
            "documentary contribution, not by shared source or actor alone. "
            "If no existing section fits a relevant subject, propose a precise "
            "new chapter using new_section_title. Do not invent catch-all chapters. "
            "Exclude only evidence genuinely outside the subject and objective; "
            "never exclude because placement is difficult or to shorten the report. "
            'Return JSON only: {"assignments": [{"note_id": "exact id", '
            '"section_id": "existing id or null", "new_section_title": '
            '"specific title or null", "exclusion_reason": "reason or null"}]}. '
            "Exactly one of section_id, new_section_title or exclusion_reason "
            "must be a nonempty string. Account for each unassigned note once. "
            "Use the requested output language for titles and reasons."
        ),
    )
    result = extract_json_object(raw)
    assignments = result.get("assignments")
    if not isinstance(assignments, list):
        raise ValueError("DOCUMENTARY_COVERAGE_INVALID: targeted repair returned no assignments")
    expected = {note.note_id for note in missing}
    seen = set()
    sections = list(organization.sections)
    repaired_exclusions = list(exclusions)
    new_titles = {}
    for item in assignments:
        if not isinstance(item, dict):
            raise ValueError("DOCUMENTARY_COVERAGE_INVALID: invalid targeted assignment")
        note_id = item.get("note_id")
        if not isinstance(note_id, str) or note_id not in expected or note_id in seen:
            raise ValueError("DOCUMENTARY_COVERAGE_INVALID: invalid targeted note_id")
        values = [item.get(key) for key in
                  ("section_id", "new_section_title", "exclusion_reason")]
        if any(value is not None and (not isinstance(value, str) or not value.strip())
               for value in values) or sum(value is not None for value in values) != 1:
            raise ValueError("DOCUMENTARY_COVERAGE_INVALID: ambiguous targeted assignment")
        target, title, reason = values
        if target is not None:
            if target not in section_ids:
                raise ValueError("DOCUMENTARY_COVERAGE_INVALID: unknown targeted section")
        elif title is not None:
            title = title.strip()
            target = new_titles.get(title.casefold())
            if target is None:
                index = len(sections) + 1
                target = f"section-repair-{index:03d}"
                while target in section_ids:
                    index += 1
                    target = f"section-repair-{index:03d}"
                sections.append(TouchNotebookSection(
                    section_id=target, title=title, description="",
                    event_ids=[], note_ids=[],
                ))
                section_ids.add(target)
                new_titles[title.casefold()] = target
        else:
            repaired_exclusions.append({"note_id": note_id, "reason": reason.strip()})
        if target is not None:
            for index, section in enumerate(sections):
                if section.section_id == target:
                    sections[index] = section.model_copy(update={
                        "note_ids": list(section.note_ids) + [note_id],
                    })
                    break
        seen.add(note_id)
    if seen != expected:
        raise ValueError("DOCUMENTARY_COVERAGE_INVALID: incomplete targeted repair "
                         + json.dumps(sorted(expected - seen)))
    repaired = organization.model_copy(update={"sections": sections})
    _validate_organization_coverage(repaired, notes, repaired_exclusions)
    logger.info("TOUCH_NOTEBOOK_TARGETED_REPAIR note_ids=%s", sorted(seen))
    return repaired, repaired_exclusions


def _validate_organization_coverage(organization, notes, exclusions):
    """Account for all input evidence before any downstream repair."""
    expected = {note.note_id for note in notes}
    if not isinstance(exclusions, list):
        raise ValueError("DOCUMENTARY_COVERAGE_INVALID: excluded_notes must be an array")
    excluded = {}
    for item in exclusions:
        if not isinstance(item, dict) or set(item) != {"note_id", "reason"}:
            raise ValueError("DOCUMENTARY_COVERAGE_INVALID: invalid exclusion entry")
        note_id, reason = item["note_id"], item["reason"]
        if not isinstance(note_id, str) or note_id not in expected:
            raise ValueError("DOCUMENTARY_COVERAGE_INVALID: unknown excluded note_id")
        if note_id in excluded:
            raise ValueError("DOCUMENTARY_COVERAGE_INVALID: duplicated exclusion " + note_id)
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("DOCUMENTARY_COVERAGE_INVALID: exclusion reason missing " + note_id)
        excluded[note_id] = reason.strip()
    events = {event.event_id: event for event in organization.events}
    if len(events) != len(organization.events):
        raise ValueError("DOCUMENTARY_COVERAGE_INVALID: duplicated event_id")
    section_ids = [section.section_id for section in organization.sections]
    if len(section_ids) != len(set(section_ids)):
        raise ValueError("DOCUMENTARY_COVERAGE_INVALID: duplicated section_id")
    placements = []
    placement_locations = {}
    referenced_events = []
    for section in organization.sections:
        placements.extend(section.note_ids)
        for note_id in section.note_ids:
            placement_locations.setdefault(note_id, []).append({
                "section_id": section.section_id,
                "section_title": section.title,
                "placement": "direct",
            })
        for event_id in section.event_ids:
            if event_id not in events:
                raise ValueError("DOCUMENTARY_COVERAGE_INVALID: unknown event " + event_id)
            referenced_events.append(event_id)
            placements.extend(events[event_id].note_ids)
            for note_id in events[event_id].note_ids:
                placement_locations.setdefault(note_id, []).append({
                    "section_id": section.section_id,
                    "section_title": section.title,
                    "event_id": event_id,
                    "placement": "event",
                })
    if len(referenced_events) != len(set(referenced_events)):
        raise ValueError("DOCUMENTARY_COVERAGE_INVALID: event placed multiple times")
    if set(events) != set(referenced_events):
        raise ValueError(
            "DOCUMENTARY_COVERAGE_INVALID: unattached event_ids "
            + json.dumps(sorted(set(events) - set(referenced_events)))
            + ". Attach these events to appropriate existing sections."
        )
    if len(placements) != len(set(placements)):
        duplicates = {
            note_id: locations
            for note_id, locations in placement_locations.items()
            if len(locations) > 1
        }
        raise ValueError(
            "DOCUMENTARY_COVERAGE_INVALID: note placed multiple times: "
            + json.dumps(duplicates, ensure_ascii=False)
            + ". For each listed note_id, retain exactly one primary placement "
            "according to its actual contribution and the chapter scopes. "
            "Remove only redundant references, never the evidence note. "
            "A note inside a referenced event must not also be listed directly "
            "in a section. Preserve all other correct placements and chapters; "
            "return the complete organization JSON."
        )
    placed = set(placements)
    unknown = placed - expected
    if unknown:
        raise ValueError("DOCUMENTARY_COVERAGE_INVALID: unknown notes " + json.dumps(sorted(unknown)))
    secondary = set()
    for item in organization.timeline:
        secondary.update(item.note_ids)
    for item in organization.contradictions:
        secondary.update(item.note_ids)
    overlap = set(excluded) & (placed | secondary)
    if overlap:
        raise ValueError("DOCUMENTARY_COVERAGE_INVALID: excluded notes still referenced " + json.dumps(sorted(overlap)))
    missing = expected - placed - set(excluded)
    if missing:
        raise ValueError(
            "DOCUMENTARY_COVERAGE_INVALID: omitted note_ids " + json.dumps(sorted(missing))
            + ". Place each omitted relevant note or explicitly justify its out-of-scope "
            "exclusion. Keep existing correct placements and chapters. Do not shorten "
            "the report, invent a catch-all section or treat these identifiers as examples."
        )
    for note_id, reason in excluded.items():
        logger.info("TOUCH_NOTEBOOK_EXCLUSION note_id=%s reason=%s", note_id, reason)
    return [note for note in notes if note.note_id not in excluded]


logger = logging.getLogger(__name__)


def _validate_chapter_outline(payload: dict) -> dict:
    if set(payload) != {"chapters"}:
        raise ValueError("Le plan doit contenir uniquement chapters")
    chapters = payload.get("chapters")
    if not isinstance(chapters, list) or not chapters:
        raise ValueError("Le plan documentaire est vide")
    cleaned = []
    seen_ids = set()
    seen_titles = set()
    for chapter in chapters:
        if not isinstance(chapter, dict) or set(chapter) != {
            "section_id", "title", "scope"
        }:
            raise ValueError("Chapitre de plan invalide")
        if any(not isinstance(chapter[key], str) or not chapter[key].strip()
               for key in ("section_id", "title", "scope")):
            raise ValueError("Identifiant, titre ou périmètre vide")
        chapter = {key: value.strip() for key, value in chapter.items()}
        title_key = chapter["title"].casefold()
        if chapter["section_id"] in seen_ids or title_key in seen_titles:
            raise ValueError("Chapitre de plan dupliqué")
        seen_ids.add(chapter["section_id"])
        seen_titles.add(title_key)
        cleaned.append(chapter)
    return {"chapters": cleaned}


def _prepare_chapter_outline(request, notes, model=None):
    # Keep comparison, cross-context and chronological behavior unchanged.
    enabled = os.getenv("TOUCH_NOTEBOOK_TWO_STAGE", "true").lower() in {
        "true", "1", "yes"
    }
    design = request.report_design
    if not enabled or design.report_archetype != "DOCUMENTARY_SYNTHESIS" \
            or design.organization_mode not in {"THEMATIC", "HYBRID"}:
        return None
    try:
        raw = run_llm_json(
            prompt=build_touch_notebook_outline_prompt(request, notes),
            model=model,
            temperature=0.0,
            system_prompt=TOUCH_NOTEBOOK_OUTLINE_SYSTEM_PROMPT,
        )
        outline = _validate_chapter_outline(extract_json_object(raw))
        print("TOUCH_NOTEBOOK_OUTLINE", {
            "subject": request.subject,
            "note_count": len(notes),
            "chapters": outline["chapters"],
        }, flush=True)
        return outline
    except Exception as exc:
        # An unavailable outline must not block an otherwise valid report.
        print("TOUCH_NOTEBOOK_OUTLINE_FALLBACK", {
            "subject": request.subject,
            "error": str(exc),
        }, flush=True)
        return None


def _review_single_section_navigation(
    request: TouchNotebookRequest,
    organization: TouchNotebookOrganizationResult,
    notes: list[TouchEvidenceNote],
    model: Optional[str] = None,
) -> Optional[str]:
    """Review only umbrella plans; never change evidence selection."""

    if len(organization.sections) != 1:
        return None

    placed_ids = set(organization.sections[0].note_ids)
    event_ids = set(organization.sections[0].event_ids)
    for event in organization.events:
        if event.event_id in event_ids:
            placed_ids.update(event.note_ids)

    placed_notes = [
        note.model_dump(mode="json")
        for note in notes
        if note.note_id in placed_ids
    ]

    if len(placed_notes) < 2:
        return None

    payload = {
        "subject": request.subject,
        "objective": request.objective,
        "report_design": request.report_design.model_dump(mode="json"),
        "organization": organization.model_dump(mode="json"),
        "placed_notes": placed_notes,
    }

    raw = run_llm_json(
        prompt=(
            "Review this single-section documentary plan. "
            "Return JSON with needs_reorganization (boolean), "
            "reason (string), and suggested_chapters (array of objects "
            "with title and example_note_ids).\n\n"
            + json.dumps(payload, ensure_ascii=False)
        ),
        model=model,
        temperature=0.0,
        system_prompt=(
            "You review chapter navigation, not evidence quality or coverage. "
            "Accept one section for a coherent narrow subject, even when it "
            "contains many notes or several complementary mechanisms. "
            "Request reorganization only when the placed notes document "
            "multiple substantial subjects readers would consult independently. "
            "A common company name alone does not make those subjects coherent. "
            "Do not demand one chapter per product, function, event or axis. "
            "Group closely related developments into broad useful chapters. "
            "Do not target a chapter count, note quota or report length. "
            "Do not add, remove, rewrite or reassess notes. "
            "Support each suggested chapter with exact placed note identifiers. "
            "If the split is uncertain or would create tiny fragments, accept "
            "the existing structure. Return only the requested JSON."
        ),
    )

    # This is an advisory review. An unavailable or malformed review
    # must not turn an otherwise valid notebook into a generation failure.
    try:
        review = extract_json_object(raw)
    except (ValueError, TypeError, AttributeError):
        return None

    if review.get("needs_reorganization") is not True:
        return None

    chapters = review.get("suggested_chapters")
    if not isinstance(chapters, list):
        return None

    valid_chapters = []
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        title = chapter.get("title")
        example_ids = chapter.get("example_note_ids")
        if (
            isinstance(title, str)
            and title.strip()
            and isinstance(example_ids, list)
            and example_ids
            and all(isinstance(value, str) and value in placed_ids
                    for value in example_ids)
        ):
            valid_chapters.append({
                "title": title.strip(),
                "example_note_ids": example_ids,
            })

    if len(valid_chapters) < 2:
        return None

    return (
        "SINGLE_SECTION_NAVIGATION: The placed evidence supports distinct "
        "chapters. Suggested groupings (guidance, not mandatory titles): "
        + json.dumps(valid_chapters, ensure_ascii=False)
        + ". Reorganize the same included notes into coherent chapters. "
        "Preserve exactly these primary-placement note_ids: "
        + json.dumps(sorted(placed_ids))
        + ". Example identifiers are examples, not a selected subset. "
        "Do not add or exclude notes, rewrite statements, or create one "
        "section per mechanism. Keep related developments together."
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


def _validate_note_assignment_batch(payload, notes, chapters):
    expected = {note.note_id for note in notes}
    if not isinstance(payload, dict) or set(payload) != {"assignments"}:
        raise ValueError("Assignment response must contain only assignments")
    items = payload["assignments"]
    if not isinstance(items, list):
        raise ValueError("assignments must be an array")
    known = {chapter["section_id"] for chapter in chapters}
    seen = set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Invalid assignment entry")
        note_id = item.get("note_id")
        if not isinstance(note_id, str) or note_id not in expected or note_id in seen:
            raise ValueError("Unknown or duplicate assigned note_id: " + str(note_id))
        seen.add(note_id)
        keys = set(item)
        if keys == {"note_id", "section_id", "reason"}:
            if not isinstance(item["section_id"], str) or item["section_id"] not in known:
                raise ValueError("Unknown destination for " + note_id)
        elif keys == {"note_id", "new_chapter_title", "new_chapter_scope", "reason"}:
            pass
        elif keys != {"note_id", "exclusion_reason"}:
            raise ValueError("Ambiguous assignment for " + note_id)
        if any(not isinstance(value, str) or not value.strip() for value in item.values()):
            raise ValueError("Empty assignment field for " + note_id)
    if expected != seen:
        raise ValueError("Missing assigned note_ids: " + json.dumps(sorted(expected - seen)))
    return items


def _organize_from_note_assignments(request, notes, certified_numbers,
                                   chapter_outline, model, max_attempts):
    chapters = [dict(chapter) for chapter in chapter_outline["chapters"]]
    assignments = []
    # Small independent classification outputs; never re-extract or rewrite notes.
    for offset in range(0, len(notes), 24):
        batch = notes[offset:offset + 24]
        original = build_touch_notebook_assignment_prompt(request, chapters, batch)
        prompt = original
        last_error = ""
        for attempt in range(max(1, max_attempts)):
            try:
                raw = run_llm_json(prompt=prompt, model=model, temperature=0.0,
                                  system_prompt=TOUCH_NOTEBOOK_ASSIGNMENT_SYSTEM_PROMPT)
                items = _validate_note_assignment_batch(extract_json_object(raw), batch, chapters)
                break
            except (ValueError, TypeError) as exc:
                last_error = str(exc)
                print("TOUCH_NOTEBOOK_ASSIGNMENT_BATCH_ERROR", {
                    "subject": request.subject, "offset": offset,
                    "attempt": attempt + 1, "error": last_error,
                }, flush=True)
                prompt = build_retry_prompt(original_prompt=original, error=last_error)
        else:
            raise ValueError("Échec de l’affectation des notes : " + last_error)
        for item in items:
            if "new_chapter_title" in item:
                title = item["new_chapter_title"].strip()
                chapter = next((c for c in chapters if c["title"].casefold() == title.casefold()), None)
                if chapter is None:
                    chapter_id = "section-added-" + str(len(chapters) + 1)
                    while any(c["section_id"] == chapter_id for c in chapters):
                        chapter_id += "-new"
                    chapter = {"section_id": chapter_id, "title": title,
                               "scope": item["new_chapter_scope"].strip()}
                    chapters.append(chapter)
                item = {"note_id": item["note_id"], "section_id": chapter["section_id"],
                        "reason": item["reason"]}
            assignments.append(item)
    destinations = {c["section_id"]: [] for c in chapters}
    exclusions = []
    for item in assignments:
        if "exclusion_reason" in item:
            exclusions.append({"note_id": item["note_id"], "reason": item["exclusion_reason"]})
        else:
            destinations[item["section_id"]].append(item["note_id"])
    sections = [TouchNotebookSection(section_id=c["section_id"], title=c["title"],
                                    description="", note_ids=destinations[c["section_id"]],
                                    event_ids=[], number_ids=[])
                for c in chapters if destinations[c["section_id"]]]
    organization = TouchNotebookOrganizationResult(sections=sections)
    retained = _validate_organization_coverage(organization, notes, exclusions)
    if not retained:
        raise ValueError("Aucune note pertinente après affectation documentaire")
    # Assessment is a separate task with no permission to modify the plan.
    assessment_prompt = json.dumps({
        "subject": request.subject, "objective": request.objective,
        "output_language": request.output_language,
        "retained_notes": [n.model_dump(mode="json") for n in retained],
    }, ensure_ascii=False)
    assessment = {}
    for attempt in range(max(1, max_attempts)):
        try:
            raw = run_llm_json(prompt=assessment_prompt, model=model, temperature=0.0,
                              system_prompt=TOUCH_NOTEBOOK_ASSESSMENT_SYSTEM_PROMPT)
            payload = extract_json_object(raw)
            if set(payload) != {"corpus_summary", "corpus_strengths", "corpus_limits"}:
                raise ValueError("Invalid corpus assessment fields")
            validated = TouchNotebookOrganizationResult.model_validate(payload)
            assessment = {key: getattr(validated, key) for key in payload}
            break
        except (ValueError, TypeError) as exc:
            print("TOUCH_NOTEBOOK_ASSESSMENT_ERROR", {
                "subject": request.subject, "attempt": attempt + 1, "error": str(exc),
            }, flush=True)
    # A failed assessment cannot destroy a valid classified corpus.
    organization = organization.model_copy(update=assessment)
    print("TOUCH_NOTEBOOK_ASSIGNMENT", {
        "subject": request.subject, "mode": "NOTE_MAPPING", "used_outline": True,
        "input_note_count": len(notes), "retained_note_count": len(retained),
        "excluded_notes": exclusions, "assignments": assignments,
        "sections": [s.model_dump(mode="json") for s in sections], "events": [],
    }, flush=True)
    return _build_notebook(request, organization, retained, certified_numbers)


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

    chapter_outline = _prepare_chapter_outline(request, notes, model)
    if chapter_outline is not None:
        return _organize_from_note_assignments(
            request, notes, certified_numbers, chapter_outline, model, max_attempts,
        )

    original_prompt = (
        build_touch_notebook_organization_prompt(

            request=request,

            notes=notes,
            chapter_outline=chapter_outline,

        )
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

        parsed = None
        organization = None
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

            organization = (
                TouchNotebookOrganizationResult
                .model_validate(
                    normalized_payload
                )
            )
            
            organization = _normalize_unattached_events(organization)

            exclusions = parsed.get("excluded_notes", [])
            try:
                retained_notes = _validate_organization_coverage(
                    organization, notes, exclusions,
                )
            except ValueError as coverage_error:
                # After the normal retry, repair only missing assignments.
                # Other validation errors remain blocking.
                if attempt + 1 < attempts or "omitted note_ids" not in str(coverage_error):
                    raise
                organization, exclusions = _repair_remaining_note_assignments(
                    request, organization, notes, exclusions, model,
                )
                retained_notes = _validate_organization_coverage(
                    organization, notes, exclusions,
                )

            _validate_comparative_organization(
                request=request,
                organization=organization,
            )
            
            # Review only the first attempt, and only when a retry is
            # available. Avoid repeated reviews and new blocking failures.
            if chapter_outline is None and attempt == 0 and attempts > 1:
                navigation_feedback = _review_single_section_navigation(
                    request=request,
                    organization=organization,
                    notes=retained_notes,
                    model=model,
                )
                if navigation_feedback:
                    prompt = build_retry_prompt(
                        original_prompt=original_prompt,
                        error=navigation_feedback,
                    )
                    continue

            print("TOUCH_NOTEBOOK_ASSIGNMENT", {
                "subject": request.subject,
                "attempt": attempt + 1,
                "used_outline": chapter_outline is not None,
                "input_note_count": len(notes),
                "retained_note_count": len(retained_notes),
                "excluded_notes": exclusions,
                "sections": [section.model_dump(mode="json")
                             for section in organization.sections],
                "events": [event.model_dump(mode="json")
                           for event in organization.events],
            }, flush=True)

            return _build_notebook(

                request=request,

                organization=(
                    organization
                ),

                notes=retained_notes,

                certified_numbers=(
                    certified_numbers
                ),

            )

        except Exception as exc:

            last_error = str(
                exc
            )
            print("TOUCH_NOTEBOOK_ORGANIZATION_ERROR", {
                "subject": request.subject,
                "attempt": attempt + 1,
                "error": last_error,
            }, flush=True)

            if (
                attempt + 1
                >= attempts
            ):

                break

            repair_context = last_error
            if isinstance(parsed, dict):
                previous_plan = dict(parsed)
                if organization is not None:
                    previous_plan.update(organization.model_dump(mode="json"))
                repair_context += (
                    "\nPrevious organization to repair (return complete JSON):\n"
                    + json.dumps(previous_plan, ensure_ascii=False)
                )
            prompt = build_retry_prompt(

                original_prompt=(
                    original_prompt
                ),

                error=repair_context,

            )

    raise ValueError(
        "Échec de l’organisation du notebook "
        f"après {attempts} tentative(s) : "
        f"{last_error}"
    )
