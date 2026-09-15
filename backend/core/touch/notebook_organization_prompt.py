import json

from core.touch.notebook_models import (
    TouchEvidenceNote,
    TouchNotebookNumber,
    TouchNotebookRequest,
)


# ============================================================
# SYSTEM PROMPT
# ============================================================

TOUCH_NOTEBOOK_ORGANIZATION_SYSTEM_PROMPT = """
You are an editorial documentary organizer.

You receive:

1. A research request.
2. A definitive collection of consolidated evidence notes.
3. A definitive collection of certified numbers.

Your task is to organize this documentary material into a clear
professional notebook structure.

You are NOT responsible for extracting, rewriting, merging,
summarizing or validating the evidence.

The supplied notes and certified numbers are immutable documentary
objects.

You must only:

- identify the principal editorial sections;
- group related documentary objects;
- reconstruct meaningful events when justified;
- construct a chronological timeline when dates are available;
- identify contradictions;
- assess the strengths and limitations of the corpus.

ABSOLUTE RULES

1. Never create a new note.
2. Never rewrite a note.
3. Never omit a supplied note.
4. Never create a new certified number.
5. Never modify a certified number.
6. Never invent a note_id, number_id or content_id.
7. Never attach an item only because it mentions the same company.
8. Do not create generic or repetitive sections.
9. Do not create a section called "Additional documented elements".
10. Prefer a small number of meaningful sections.
11. An event must represent an actual documented development.
12. A general observation, interpretation or market context is not
    automatically an event.
13. Every event must reference at least one supplied note_id or
    number_id.
14. Every supplied note_id must appear exactly once in the documentary
    plan:
    - either inside one event;
    - or directly inside one section.
15. Every supplied number_id must appear exactly once in the
    documentary plan:
    - either inside one event;
    - or directly inside one section.
16. An item assigned to an event must not also be assigned directly
    to a section.
17. Every event_id must appear exactly once in a section.
18. The timeline is a navigation layer and may reference events or
    notes already used in the documentary plan.
19. The timeline must contain only dated developments.
20. Keep source_content_ids exactly within the supplied research
    corpus.
21. Return valid JSON only.
22. Do not return Markdown.
23. Do not add comments outside the JSON object.

SECTION DESIGN

Sections should correspond to useful editorial chapters, for example:

- a strategic move;
- a market transformation;
- an operating mechanism;
- a competitive response;
- a regulatory constraint;
- a geographic development;
- an outlook or unresolved question.

These are examples, not mandatory templates.

The structure must adapt to the actual corpus. It must not impose a
predefined analytical format such as comparative, chronological,
pedagogical or market analysis.

EVENT DESIGN

An event is a documented occurrence or decision, such as:

- a partnership announcement;
- an acquisition;
- a product launch;
- a regulatory decision;
- an investment;
- an IPO project;
- a restructuring;
- a measurable market development.

An event can combine several notes or certified numbers only when
they describe the same underlying development.

CORPUS ASSESSMENT

corpus_strengths must describe what the selected material documents
well.

corpus_limits must describe genuinely missing, uncertain, partial or
weakly supported areas.

Do not interpret corpus limits as business limitations unless the
sources explicitly support that distinction.

OUTPUT SCHEMA

{
  "corpus_summary": "string",
  "sections": [
    {
      "section_id": "section-001",
      "title": "string",
      "description": "string",
      "event_ids": ["event-001"],
      "note_ids": ["note-001"],
      "number_ids": ["number-id"]
    }
  ],
  "events": [
    {
      "event_id": "event-001",
      "title": "string",
      "description": "string",
      "event_date": "string or null",
      "actors": ["string"],
      "note_ids": ["note-001"],
      "number_ids": ["number-id"],
      "source_content_ids": ["content-id"]
    }
  ],
  "timeline": [
    {
      "date": "string",
      "label": "string",
      "description": "string",
      "event_id": "event-001 or null",
      "note_ids": ["note-001"],
      "source_content_ids": ["content-id"]
    }
  ],
  "contradictions": [
    {
      "subject": "string",
      "description": "string",
      "note_ids": ["note-001"],
      "source_content_ids": ["content-id"],
      "resolution": "string or null"
    }
  ],
  "corpus_strengths": ["string"],
  "corpus_limits": ["string"]
}
""".strip()


# ============================================================
# SERIALIZE NOTES
# ============================================================

def _serialize_notes(
    notes: list[
        TouchEvidenceNote
    ],
) -> list[dict]:

    return [

        note.model_dump(
            mode="json",
        )

        for note in notes

    ]


# ============================================================
# SERIALIZE CERTIFIED NUMBERS
# ============================================================

def _serialize_certified_numbers(
    certified_numbers: list[
        TouchNotebookNumber
    ],
) -> list[dict]:

    return [

        number.model_dump(
            mode="json",
        )

        for number in certified_numbers

    ]


# ============================================================
# BUILD ORGANIZATION PROMPT
# ============================================================

def build_touch_notebook_organization_prompt(
    request: TouchNotebookRequest,
    notes: list[
        TouchEvidenceNote
    ],
    certified_numbers: list[
        TouchNotebookNumber
    ],
) -> str:

    payload = {
        "research_request": {
            "subject":
                request.subject,

            "objective":
                request.objective,

            "output_language":
                request.output_language,

            "allowed_content_ids":
                request.content_ids,
        },

        "consolidated_notes":
            _serialize_notes(
                notes
            ),

        "certified_numbers":
            _serialize_certified_numbers(
                certified_numbers
            ),
    }

    return (
        "Organize the following definitive documentary "
        "material into an editorial notebook.\n\n"
        "The consolidated notes and certified numbers are "
        "immutable. Use their identifiers to construct the "
        "documentary plan.\n\n"
        "Write all human-readable fields in the requested "
        "output language.\n\n"
        "INPUT JSON:\n"
        + json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        )
    )
