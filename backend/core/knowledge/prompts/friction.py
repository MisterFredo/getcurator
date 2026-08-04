# backend/core/knowledge/prompts/friction.py

from ..models import (
    KnowledgeBlock,
    KnowledgeObservation,
    KnowledgeEntityType,
)


# ============================================================
# PROMPT
# ============================================================

def build_friction_prompt(
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

- confirms an existing limitation
- enriches an existing limitation
- replaces an outdated limitation
- reveals a new structural friction

Your objective is NOT to summarize today's observations.

Your objective is to identify what limits, slows down or weakens this entity.

--------------------------------------------------
RULES

Every note must describe one durable friction.

Focus on:

- structural limitations
- competitive pressure
- regulatory constraints
- technological limitations
- operational complexity
- adoption barriers
- organizational weaknesses
- execution risks
- dependency risks

Describe what prevents the entity from fully achieving its objectives.

Do not describe market trends.

Do not explain how the entity works.

Do not explain strategic implications.

Ignore temporary issues.

Ignore isolated incidents.

If no durable friction exists, do not invent one.

Merge similar frictions.

Rewrite notes when necessary.

Delete obsolete frictions.

Keep only durable knowledge.

Keep the notebook concise.

Quality is more important than quantity.

--------------------------------------------------
OUTPUT

Return the complete updated notebook.

Only bullet points.

Each bullet must describe one durable structural friction affecting this entity.

No introduction.

No conclusion.

No numbering.

No markdown.

No explanations.
""".strip()
