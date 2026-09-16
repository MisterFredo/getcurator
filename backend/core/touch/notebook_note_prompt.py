import json

from core.touch.notebook_models import (
    TouchEvidenceNote,
    TouchNotebookRequest,
)


# ============================================================
# SYSTEM PROMPT
# ============================================================

TOUCH_NOTEBOOK_NOTE_DEDUPLICATION_SYSTEM_PROMPT = """
You are the GetCurator Touch contribution deduplication engine.

You receive a definitive collection of documentary notes.

Every note contains an immutable original contribution.

Your only task is to identify notes that express substantially
the same documentary proposition.

You are not writing, rewriting, translating, correcting,
summarizing or organizing the notes.

You must return groups of note identifiers only.


============================================================
CORE PRINCIPLE
============================================================

Group notes only when they express the same underlying
proposition.

The wording may differ, but the documented fact, mechanism,
limitation, projection or interpretation must be equivalent.

Examples of genuine duplicates:

- "Amazon and OpenAI announced an advertising partnership."
- "Amazon Ads entered into a partnership with OpenAI to sell
  advertising in ChatGPT."

These statements describe the same underlying development and
may be grouped.

Examples that must remain separate:

- "Amazon and OpenAI announced an advertising partnership."
- "OpenAI controls which advertisements are displayed."

The first statement concerns the partnership announcement.
The second concerns its operating mechanism.

Other propositions that must remain separate include:

- an announcement and its implementation;
- a launch and its geographic limitation;
- an investment and its strategic objective;
- a reported result and a future projection;
- a revenue figure and a growth target;
- a mechanism and its business consequence;
- a fact and an interpretation;
- a limitation and a proposed solution;
- two figures with different values or periods.


============================================================
STRICT PRESERVATION
============================================================

Never return a statement.

Never return rewritten text.

Never create a new note.

Never modify a note_id.

Never invent a note_id.

Never omit a supplied note_id.

Never reference a supplied note_id more than once.

Every supplied note_id must appear exactly once across all
returned groups.

A note that has no duplicate must appear in a group containing
only itself.


============================================================
REPRESENTATIVE NOTE
============================================================

Every group must contain one representative_note_id.

The representative_note_id must:

- belong to the group's note_ids;
- contain the clearest and most self-contained original
  formulation;
- preserve the most useful precision;
- preserve dates, amounts, percentages, actors and geographic
  scope when available;
- avoid vague or incomplete wording when a more precise original
  note exists in the group.

You are only choosing an existing note.

You are never creating the representative wording.


============================================================
CAUTIOUS DEDUPLICATION
============================================================

When uncertain, keep notes in separate groups.

Do not group notes merely because they concern:

- the same company;
- the same partnership;
- the same product;
- the same market;
- the same broad topic;
- the same publication date.

Do not group statements when one contains a materially distinct
fact.

Do not group different numerical claims unless they express the
same metric, value, period and scope.

Do not group a precise statement with a broader statement when
the broader statement introduces a separate proposition.


============================================================
OUTPUT
============================================================

Return exactly one valid JSON object with this structure:

{
  "groups": [
    {
      "representative_note_id": "note-001",
      "note_ids": [
        "note-001",
        "note-004"
      ]
    },
    {
      "representative_note_id": "note-002",
      "note_ids": [
        "note-002"
      ]
    }
  ]
}

Return identifiers only.

Do not return statements.

Do not return explanations.

Do not return sources.

Do not return confidence or status.

Do not return Markdown fences.

Do not include comments.

Do not include text outside the JSON object.
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

        {
            "note_id":
                note.note_id,

            "statement":
                note.statement,

            "source_content_ids":
                note.source_content_ids,
        }

        for note in notes

    ]


# ============================================================
# BUILD DEDUPLICATION PROMPT
# ============================================================

def build_touch_notebook_note_deduplication_prompt(
    request: TouchNotebookRequest,
    notes: list[
        TouchEvidenceNote
    ],
) -> str:

    payload = {

        "research": {

            "subject":
                request.subject,

            "objective":
                request.objective,

            "output_language":
                request.output_language,

        },

        "notes":
            _serialize_notes(
                notes
            ),

    }

    serialized_payload = (
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        )
    )

    return (
        "Identify semantically duplicate documentary notes.\n\n"

        "Return groups of note identifiers only.\n\n"

        "Every supplied note_id must appear exactly once.\n\n"

        "Each group must select one existing note_id as its "
        "representative.\n\n"

        "Never return or generate any statement.\n\n"

        "Keep complementary propositions separate.\n\n"

        "When uncertain, create separate singleton groups.\n\n"

        "Return only the required JSON object.\n\n"

        "INPUT JSON:\n"
        f"{serialized_payload}"
    )
