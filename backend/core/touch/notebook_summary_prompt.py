import json

from core.touch.notebook_models import (
    TouchCorpusNotebook,
    TouchEvidenceNote,
    TouchNotebookRequest,
)


# ============================================================
# SYSTEM PROMPT
# ============================================================

TOUCH_NOTEBOOK_SUMMARY_SYSTEM_PROMPT = """
You are the GetCurator Touch executive summary engine.

You receive:

1. A research request.
2. An organized documentary plan.
3. A definitive collection of deduplicated evidence notes.

Your task is to produce a concise, evidence-grounded executive
summary.

The executive summary may synthesize and reformulate the
evidence, but every factual clause must be supported by the
referenced notes.

You must not use external knowledge.


============================================================
PURPOSE
============================================================

The executive summary must allow a professional reader to
understand the essential documented information without reading
the entire notebook.

It is not:

- an introduction;
- a table of contents;
- a description of the corpus;
- an opinion;
- a recommendation;
- a generic market analysis;
- a repetition of section titles.

It must communicate the most important documented facts,
mechanisms, figures, developments, limitations and outlooks.


============================================================
GROUNDING
============================================================

Every summary item must reference one or more supplied note_ids.

Every factual element in the statement must be supported by
those notes.

Never invent:

- an actor;
- an action;
- a date;
- a geography;
- an amount;
- a percentage;
- a causal relationship;
- a consequence;
- a projection;
- a limitation;
- a recommendation.

Do not strengthen the certainty of the evidence.

Preserve distinctions between:

- established facts;
- reported results;
- forecasts;
- targets;
- assumptions;
- uncertainties;
- interpretations.

A projection must remain a projection.

A target must remain a target.

An allegation must remain attributed when attribution is
required.


============================================================
EDITORIAL QUALITY
============================================================

Each item must:

- contain one or two sentences;
- communicate one central idea;
- be precise and information-dense;
- remain understandable without the full notebook;
- preserve useful actors, dates, amounts and geographic scope;
- use the requested output language;
- avoid unnecessary introductory wording.

An item may synthesize several complementary notes when they
support one coherent message.

Do not combine unrelated propositions merely to reduce the
number of items.

Prefer concrete information over general interpretation.


============================================================
FORBIDDEN FORMULATIONS
============================================================

Do not write generic formulations such as:

- "The corpus shows that..."
- "The sources highlight..."
- "It is important to note that..."
- "Several trends emerge..."
- "This marks a major turning point..."
- "This could transform the market..."
- "This partnership illustrates the growing importance of..."
- "Le corpus montre que..."
- "Les sources soulignent..."
- "Il est important de noter que..."
- "Plusieurs tendances se dégagent..."
- "Cela marque un tournant majeur..."
- "Cette évolution pourrait transformer le marché..."
- "Ce partenariat illustre l'importance croissante de..."

Do not describe the research process.

Do not announce what the notebook contains.

State the documented information directly.


============================================================
SELECTION
============================================================

When enough evidence is available, return between four and six
summary items.

Select the smallest number of items needed to cover the central
documented insights.

Seek useful balance across the corpus, when supported:

- the central development;
- the operating mechanism;
- the scale or key quantified evidence;
- the strategic objective or documented consequence;
- an important limitation, uncertainty or unresolved issue.

This is not a mandatory template.

Adapt the selection to the actual documentary material.

Do not create a weak item merely to fill a category.

Do not reuse the same note_id in several summary items.

Not every supplied note must appear in the executive summary.


============================================================
LENGTH
============================================================

Be as concise as the documented information allows; use at most 70 words »

Use at most two sentences per item.

Avoid repeating the same actor, context or introductory phrase
across several items.

The complete executive summary should remain concise enough for
the first page of a professional document.


============================================================
OUTPUT
============================================================

Return exactly one valid JSON object with this structure:

{
  "items": [
    {
      "statement": "Precise evidence-grounded synthesis",
      "note_ids": [
        "note-001",
        "note-004"
      ]
    }
  ]
}

Return only statement and note_ids.

Do not return summary_id.

Do not return source_content_ids.

Do not return section_ids.

Do not return event_ids.

Do not return Markdown fences.

Do not include comments.

Do not include text outside the JSON object.
""".strip()


# ============================================================
# SERIALIZE NOTE
# ============================================================

def _serialize_note(
    note: TouchEvidenceNote,
) -> dict:

    return {

        "note_id":
            note.note_id,

        "note_type":
            note.note_type,

        "statement":
            note.statement,

        "confidence":
            note.confidence,

        "status":
            note.status,

        "source_content_ids":
            note.source_content_ids,

    }


# ============================================================
# BUILD SUMMARY PROMPT
# ============================================================

def build_touch_notebook_summary_prompt(
    request: TouchNotebookRequest,
    notebook: TouchCorpusNotebook,
) -> str:

    notes_by_id = {

        note.note_id:
            note

        for note in notebook.notes

    }

    sections = [

        {
            "section_id":
                section.section_id,

            "title":
                section.title,

            "event_ids":
                section.event_ids,

            "standalone_note_ids":
                section.note_ids,
        }

        for section in notebook.sections

    ]

    events = [

        {
            "event_id":
                event.event_id,

            "title":
                event.title,

            "event_date":
                event.event_date,

            "actors":
                event.actors,

            "note_ids":
                event.note_ids,
        }

        for event in notebook.events

    ]

    notes = [

        _serialize_note(
            note
        )

        for note in notebook.notes

    ]

    available_note_count = len(
        notes_by_id
    )

    minimum_item_count = (
        4
        if available_note_count >= 4
        else available_note_count
    )

    maximum_item_count = min(
        6,
        available_note_count,
    )

    payload = {

        "research_request": {

            "subject":
                request.subject,

            "objective":
                request.objective,

            "output_language":
                request.output_language,

        },

        "constraints": {

            "minimum_item_count":
                minimum_item_count,

            "maximum_item_count":
                maximum_item_count,

            "maximum_words_per_item":
                55,

            "maximum_sentences_per_item":
                2,

        },

        "documentary_plan": {

            "sections":
                sections,

            "events":
                events,

        },

        "evidence_notes":
            notes,

    }

    serialized_payload = (
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        )
    )

    return (
        "Produce an evidence-grounded executive summary from "
        "the organized documentary notebook.\n\n"

        "Every factual clause must be supported by the "
        "referenced note_ids.\n\n"

        "Write concrete, information-dense statements. Do not "
        "describe the corpus or the research process.\n\n"

        "Do not use the same note_id in more than one item.\n\n"

        "Respect the supplied item-count and length "
        "constraints.\n\n"

        "Return only the required JSON object.\n\n"

        "INPUT JSON:\n"
        f"{serialized_payload}"
    )
