# backend/core/knowledge/prompts/mecanique.py

from ..models import (
    KnowledgeBlock,
    KnowledgeObservation,
    KnowledgeEntityType,
)


# ============================================================
# PROMPT
# ============================================================

def build_mecanique_prompt(
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

1. Update an existing explanation if possible.
2. Merge with an existing explanation if both describe the same operating mechanism.
3. Replace an outdated explanation if the new observation provides a better understanding.
4. Create a new explanation only if the observation reveals a genuinely new long-term operating mechanism that cannot fit into any existing note.

Your objective is NOT to summarize today's observations.

Your objective is to continuously improve your understanding of how this entity actually works.

--------------------------------------------------
RULES

Every note must describe this entity.

Every note must explain one durable operating mechanism.

Focus on:

- business model
- operating model
- decision process
- value creation
- commercial mechanisms
- technological mechanisms
- organizational mechanisms
- competitive mechanisms

Always explain HOW the entity works.

Do not describe market trends.

Do not explain strategic implications.

Do not describe limitations.

The notebook is a long-term memory, not a collection of observations.

Prefer improving existing explanations over creating new ones.

A new bullet should be rare.

Whenever two notes describe the same underlying mechanism, merge them into a stronger and more complete explanation.

Rewrite existing notes instead of appending information.

Delete obsolete or redundant explanations.

Keep only durable mechanisms.

Ignore isolated announcements.

Ignore temporary events.

Ignore communication.

The notebook should become more accurate over time, not significantly longer.

Quality is more important than quantity.

Even if the notebook is already correct, improve wording, merge overlapping explanations and simplify the structure whenever possible.

--------------------------------------------------
OUTPUT

Return the complete updated notebook.

Only bullet points.

Each bullet must explain one durable operating mechanism of this entity.

No introduction.

No conclusion.

No numbering.

No markdown.

No explanations.
""".strip()
