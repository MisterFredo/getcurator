# backend/core/knowledge/prompts/enjeu.py

from ..models import (
    KnowledgeBlock,
    KnowledgeObservation,
    KnowledgeEntityType,
)


# ============================================================
# PROMPT
# ============================================================

def build_enjeu_prompt(
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

- confirms an existing strategic implication
- enriches an existing implication
- replaces an outdated implication
- reveals a new strategic implication

Your objective is NOT to summarize today's observations.

Your objective is to explain what these observations reveal strategically.

--------------------------------------------------
RULES

Every note must explain why this matters.

Focus on:

- strategic positioning
- competitive advantage
- competitive threats
- long-term opportunities
- structural market evolution
- business impact
- strategic implications

Do not describe how things work.

Do not describe isolated events.

Do not describe market trends.

Do not describe limitations.

Extract the underlying strategic meaning.

Merge similar implications.

Rewrite implications when necessary.

Delete obsolete implications.

Keep only durable strategic knowledge.

Keep the notebook concise.

Quality is more important than quantity.

--------------------------------------------------
OUTPUT

Return the complete updated notebook.

Only bullet points.

Each bullet must describe one durable strategic implication.

No introduction.

No conclusion.

No numbering.

No markdown.

No explanations.
""".strip()
