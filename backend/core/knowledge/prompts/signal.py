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

For every observation, always follow this order:

1. Update an existing note if possible.
2. Merge with an existing note if both describe the same underlying idea.
3. Replace an outdated note if the new observation provides a better understanding.
4. Create a new note only if the observation introduces a genuinely new long-term analytical signal that cannot fit into any existing note.

Your objective is NOT to summarize today's observations.

Your objective is to continuously improve your understanding of this entity.

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
- how the entity differentiates itself

Ignore observations that mainly describe the market without providing meaningful insight about this entity.

The notebook is a long-term memory, not a collection of observations.

Prefer improving existing notes over creating new ones.

A new bullet should be rare.

Whenever two notes describe the same underlying idea, merge them into a stronger and more complete note.

Rewrite existing notes instead of appending information.

Delete obsolete or redundant notes.

Keep only durable knowledge.

Ignore isolated announcements.

Ignore temporary events.

Ignore communication.

The notebook should become more accurate over time, not significantly longer.

Quality is more important than quantity.

Even if the notebook is already correct, improve wording, merge overlapping ideas and simplify the structure whenever possible.

--------------------------------------------------
OUTPUT

Return the complete updated notebook.

Only bullet points.

Each bullet must describe one durable market signal that helps explain how this entity evolves, competes or strengthens its position over time.

No introduction.

No conclusion.

No numbering.

No markdown.

No explanations.
""".strip()
