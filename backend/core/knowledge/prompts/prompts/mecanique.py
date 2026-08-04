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

For each observation decide whether it:

- confirms an existing explanation
- enriches an existing explanation
- replaces an outdated explanation
- reveals a new operating mechanism

Your objective is NOT to summarize today's observations.

Your objective is to explain how this entity actually works.

--------------------------------------------------
RULES

Every note must describe one durable operating mechanism.

Focus on:

- business model
- operating model
- decision process
- value creation
- competitive mechanisms
- technological mechanisms
- commercial mechanisms
- organizational mechanisms

Describe HOW things work.

Do not describe market trends.

Do not describe strategic consequences.

Do not describe limitations.

Merge similar explanations.

Rewrite explanations when necessary.

Delete obsolete explanations.

Keep only durable mechanisms.

Keep the notebook concise.

Quality is more important than quantity.

--------------------------------------------------
OUTPUT

Return the complete updated notebook.

Only bullet points.

Each bullet must explain one durable mechanism of this entity.

No introduction.

No conclusion.

No numbering.

No markdown.

No explanations.
""".strip()
