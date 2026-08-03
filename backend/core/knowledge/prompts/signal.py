# backend/core/knowledge/prompts/signal.py

from ..models import (
    KnowledgeBlock,
    KnowledgeContent,
)


# ============================================================
# PROMPT
# ============================================================

def build_signal_prompt(
    block: KnowledgeBlock,
    contents: list[KnowledgeContent],
) -> str:

    current_notes = (
        block.content.strip()
        if block.content.strip()
        else "No notes yet."
    )

    observations = []

    for content in contents:

        observations.append(f"""
TITLE
{content.title}

EXCERPT
{content.excerpt}

SIGNAL
{content.signal_analytique}
""".strip())

    observations = "\n\n--------------------------------------------------\n\n".join(
        observations,
    )

    return f"""
You are a senior strategy consultant.

You are maintaining your own professional notebook.

The notebook represents everything you currently know about this entity.

It must continuously improve.

It must never become longer.

It must become better.

--------------------------------------------------
CURRENT NOTEBOOK

{current_notes}

--------------------------------------------------
NEW OBSERVATIONS

{observations}

--------------------------------------------------
MISSION

Read every new observation.

For each observation decide whether it:

- confirms an existing note
- enriches an existing note
- replaces an outdated note
- introduces a genuinely new idea

Your objective is NOT to summarize today's observations.

Your objective is to improve your notebook.

--------------------------------------------------
RULES

Keep only durable knowledge.

Ignore isolated announcements.

Ignore temporary events.

Ignore communication.

Keep only ideas that help explain the market.

Merge similar ideas.

Rewrite notes when necessary.

Delete obsolete ideas.

Never exceed fifty bullet points.

Quality is more important than quantity.

--------------------------------------------------
OUTPUT

Return the complete updated notebook.

Only bullet points.

No introduction.

No conclusion.

No numbering.

No markdown.

No explanations.
""".strip()
