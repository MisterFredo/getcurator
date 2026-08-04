# backend/core/knowledge/prompts/signal.py

from ..models import (
    KnowledgeBlock,
    KnowledgeObservation,
    KnowledgeEntityType,
)


# ============================================================
# PROMPT
# ============================================================

def build_signal_prompt(
    entity_name: str,
    entity_type: KnowledgeEntityType,
    block: KnowledgeBlock,
    contents: list[KnowledgeObservation],
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

OBSERVATION
{content.content}
""".strip())

    observations = "\n\n--------------------------------------------------\n\n".join(
        observations,
    )

    return f"""
You are a senior strategy consultant.

Your mission is to continuously build the strategic knowledge of one entity.

--------------------------------------------------
SUBJECT

Name

{entity_name}

Type

{entity_type}

--------------------------------------------------
CURRENT NOTEBOOK

{current_notes}

--------------------------------------------------
NEW OBSERVATIONS

{observations}

--------------------------------------------------
MISSION

The notebook is dedicated exclusively to this entity.

Read every new observation.

For each observation decide whether it:

- confirms an existing note
- enriches an existing note
- replaces an outdated note
- introduces a genuinely new idea

Your objective is NOT to summarize today's observations.

Your objective is to improve your knowledge of this entity.

--------------------------------------------------
RULES

Every note must describe this entity.

Market observations are useful only if they help explain this entity.

Keep only information that helps understand:

- how the entity evolves
- how the entity behaves
- how the entity competes
- how the entity creates value
- how the entity is positioned
- how the entity differs from competitors

Ignore observations that mainly describe the market without providing meaningful insight about this entity.

Keep only durable knowledge.

Ignore isolated announcements.

Ignore temporary events.

Ignore communication.

Merge similar ideas.

Rewrite notes when necessary.

Delete obsolete ideas.

Keep the notebook concise.

Quality is more important than quantity.

If the current notebook is already correct,
do not modify it.

--------------------------------------------------
OUTPUT

Return the complete updated notebook.

Only bullet points.

Each bullet must describe one durable analytical signal about this entity.

No introduction.

No conclusion.

No numbering.

No markdown.

No explanations.
""".strip()
