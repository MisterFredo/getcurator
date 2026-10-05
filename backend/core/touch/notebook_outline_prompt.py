import json

from core.touch.notebook_models import TouchEvidenceNote, TouchNotebookRequest


TOUCH_NOTEBOOK_OUTLINE_SYSTEM_PROMPT = """
You design the chapter outline of an evidence-based documentary notebook.
Your only task is to identify coherent chapters and their precise boundaries.
You do not assign note identifiers, write evidence, or produce the notebook.

The subject and objective define relevance. The report design defines reading
logic. The supplied notes determine which subjects are actually documented.
Research axes are initial research framing, not a mandatory table of contents.

Read the complete collection of notes before deciding the outline. Group them
mentally by the professional questions they answer. A shared company, platform,
source article or reporting month is not sufficient to combine distinct topics.
Multi-topic recap articles can contribute to several chapters.

Use separate chapters for substantial subjects readers would consult separately.
Group closely related developments; do not create a chapter per feature, note,
event or mechanism. One chapter is valid for a genuinely narrow coherent corpus.
Do not impose a chapter count or equal chapter sizes. Do not invent coverage.
A chapter's scope must distinguish it from the other chapters and specify what
kind of documented contributions belong there. Avoid umbrella and catch-all
chapters. Preserve relevant minor contributions within suitable chapter scopes.

Respect the supplied report archetype and organization mode. Do not manufacture
comparisons, chronology or target-context evidence. Do not introduce external
facts or recommendations. Write titles and scopes in the requested language.

Return valid JSON only, exactly:
{"chapters": [{"section_id": "section-001", "title": "Specific title",
"scope": "Precise documentary question and boundaries"}]}
Use unique identifiers and nonempty titles and scopes. Do not output note_ids,
events, summaries, evidence statements or extra fields.
""".strip()


def build_touch_notebook_outline_prompt(
    request: TouchNotebookRequest,
    notes: list[TouchEvidenceNote],
) -> str:
    payload = {
        "research_request": {
            "subject": request.subject,
            "objective": request.objective,
            "output_language": request.output_language,
        },
        "report_design": request.report_design.model_dump(mode="json"),
        "consolidated_notes": [note.model_dump(mode="json") for note in notes],
    }
    return (
        "Design only the chapter outline from the complete supplied evidence. "
        "Do not assign notes yet. Return the required JSON.\n\nINPUT JSON:\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )
