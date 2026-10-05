import json


TOUCH_NOTEBOOK_ASSIGNMENT_SYSTEM_PROMPT = """
Classify immutable evidence notes into the supplied documentary chapters.
Your only task is to choose one primary destination for each supplied note.
Read the actual statement and context, not its identifier or source position.
A recap article may contribute notes to several different chapters.
Choose by the main development described, not incidental words such as AI,
data, performance or the company name. Measurement tools and conversion data
belong to the suitable measurement chapter; campaign configuration belongs to
campaign operation. Use the chapter scopes and the research mandate together.
When scopes overlap, choose the most specific chapter for the actual contribution.
Do not force a relevant note into an unsuitable chapter. If none fits, propose a
precise additional chapter with title and scope. Do not propose miscellaneous or
other-news chapters. Use the same title for the same missing subject.
Exclude only genuinely out-of-scope evidence, with a concrete reason. Never
exclude to shorten the report or because a chapter is missing.
Return exactly one assignment per supplied note_id, including every supplied
note_id exactly once. Do not rewrite notes, create events or write a summary.
Return JSON only: {"assignments": [{"note_id": "supplied identifier",
"section_id": "existing chapter identifier", "reason": "brief routing reason"}]}.
For a missing chapter use note_id, new_chapter_title, new_chapter_scope, reason
instead of section_id. For exclusion use note_id, exclusion_reason only.
No extra fields. Write reasons and proposed chapters in the requested language.
""".strip()


def build_touch_notebook_assignment_prompt(request, chapters, notes):
    return json.dumps({
        "subject": request.subject,
        "objective": request.objective,
        "output_language": request.output_language,
        "chapters": chapters,
        "notes_to_assign": [note.model_dump(mode="json") for note in notes],
    }, ensure_ascii=False, indent=2)


TOUCH_NOTEBOOK_ASSESSMENT_SYSTEM_PROMPT = """
Assess the supplied documentary corpus after its note placement is fixed.
Return JSON only with exactly corpus_summary (string), corpus_strengths (array
of strings) and corpus_limits (array of strings). Do not return a plan, note
assignments, events or new evidence. Write in the requested language.
Describe only the supplied retained evidence. A question initially marked as
missing is not a proven corpus limitation: reassess it against the actual notes.
Do not claim that examples of new capabilities are absent if the notes describe
such capabilities. Distinguish missing client case studies from documented
product announcements. Do not invent limitations or claim completeness.
""".strip()
