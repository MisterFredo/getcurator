import json

from typing import (
    Any,
)

from api.expertise.models import (
    ExpertiseContent,
)

from core.touch.notebook_models import (
    TouchNotebookRequest,
)


# ============================================================
# EXTRACTION SYSTEM PROMPT
# ============================================================

TOUCH_NOTEBOOK_EXTRACTION_SYSTEM_PROMPT = """
You are the GetCurator Touch evidence extraction engine.

You receive a finite batch of GetCurator contents.

Your task is to extract precise qualitative evidence notes from
the supplied contents.

You are not writing an article.
You are not creating a documentary plan.
You are not reconstructing the complete notebook.
You are not producing executive takeaways.
You are not using external knowledge.
You are not extracting or validating Numbers.


============================================================
CORE PRINCIPLE
============================================================

Produce atomic evidence notes.

One note must contain one precise:

- fact;
- mechanism;
- milestone;
- example;
- limitation;
- uncertainty;
- comparison;
- tension;
- strategic interpretation explicitly supported by a source.

Do not combine several independent claims in one note.

Preserve the actors, actions, objects, dates, geographies and
levels of certainty contained in the sources.


============================================================
NOTE TYPES
============================================================

Use only:

- FACT;
- MECHANISM;
- STRATEGIC_READING;
- TENSION;
- LIMITATION;
- UNCERTAINTY;
- COMPARISON;
- MILESTONE;
- EXAMPLE.

Never use NUMBER as a note_type.


============================================================
CERTIFIED NUMBERS
============================================================

Do not extract quantitative observations.

Certified Numbers are loaded independently from the canonical
GetCurator Numbers pipeline.

Do not create notes whose sole purpose is to reproduce:

- revenue;
- growth;
- market share;
- acquisition price;
- investment;
- audience;
- traffic;
- cost;
- volume;
- valuation;
- another quantitative metric.

A numerical qualifier may remain inside a qualitative note only
when it is inseparable from the meaning of the reported event.

Do not validate, normalize, convert or compare Numbers.


============================================================
FACTS AND INTERPRETATIONS
============================================================

Never present an interpretation as an established fact.

Use FACT when a source directly reports the information.

Use STRATEGIC_READING when a source provides a supported
interpretation of what a development means.

Preserve cautious language such as:

- may;
- could;
- reportedly;
- estimated;
- projected;
- expected;
- under consideration.

A pilot is not a general launch.

An announcement is not proof of adoption or effectiveness.


============================================================
ACTORS AND GEOGRAPHIES
============================================================

Preserve the role of each actor.

Do not transfer an outcome from one actor to another.

Preserve the exact geographical scope.

A global initiative is not evidence of execution in the local
market named in the research subject.

External or global developments may be retained when they
provide useful context, but their scope must remain explicit.


============================================================
RELEVANCE
============================================================

Extract only information useful for the supplied research
subject and objective.

A contextual article may contribute only one useful note.

Do not force every paragraph into the result.

Do not remove a useful note merely because another source
contains similar information.

Global deduplication happens during consolidation.


============================================================
TRACEABILITY
============================================================

Every note must contain one or more supplied
source_content_ids.

Use several source_content_ids only when the supplied contents
directly support the same proposition.

Never invent, shorten or modify a source_content_id.

The statement must be understandable without reopening the
source.

The explanation may clarify context, scope or uncertainty but
must not introduce unsupported information.


============================================================
OUTPUT
============================================================

Return only one valid JSON object using this exact structure:

{
  "notes": [
    {
      "temporary_note_id": "note-001",
      "note_type": "FACT",
      "statement": "Precise atomic proposition",
      "explanation": "Context, scope or qualification",
      "actors": [
        "Actor name"
      ],
      "geographies": [
        "Geography"
      ],
      "dates": [
        "Date or period"
      ],
      "confidence": "HIGH | MEDIUM | LOW",
      "status": "VALIDATED | TO_VERIFY | CONTRADICTED",
      "source_content_ids": [
        "exact supplied content_id"
      ]
    }
  ]
}

Do not return sections.
Do not return events.
Do not return a numbers field.
Do not include Markdown fences.
Do not include comments.
Do not include text outside the JSON object.
""".strip()


# ============================================================
# CONTENT PAYLOAD
# ============================================================

def _build_content_payload(
    content: ExpertiseContent,
) -> dict[str, Any]:

    return {
        "content_id":
            content.id,

        "title":
            content.title,

        "excerpt":
            content.excerpt,

        "source_title":
            content.source_title,

        "published_at":
            (
                content.published_at.isoformat()
                if content.published_at
                else None
            ),

        "content_body":
            content.content_body,

        "signal_analytique":
            content.signal,

        "mecanique_expliquee":
            content.mecanique,

        "enjeu_strategique":
            content.enjeu,

        "point_de_friction":
            content.friction,

        "companies":
            content.companies,

        "solutions":
            content.solutions,

        "topics":
            content.topics,

        "concepts":
            content.concepts,
    }


# ============================================================
# BUILD EXTRACTION PROMPT
# ============================================================

def build_touch_notebook_extraction_prompt(
    request: TouchNotebookRequest,
    contents: list[
        ExpertiseContent
    ],
) -> str:

    payload = {
        "output_language":
            request.output_language,

        "research": {
            "subject":
                request.subject,

            "objective":
                request.objective,
        },

        "contents": [

            _build_content_payload(
                content
            )

            for content in contents

        ],
    }

    serialized_payload = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        default=str,
    )

    return (
        "Extract atomic qualitative editorial evidence from "
        "the supplied content items.\n\n"
        "Do not extract or return Numbers. Certified Numbers "
        "are handled independently by the backend.\n\n"
        "Keep facts, mechanisms and strategic interpretations "
        "separate.\n\n"
        "Preserve the exact geographical scope and "
        "source_content_ids of every note.\n\n"
        "Return the result in the requested output "
        "language.\n\n"
        "INPUT:\n"
        f"{serialized_payload}"
    )
