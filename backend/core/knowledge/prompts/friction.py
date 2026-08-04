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

- confirms an existing friction
- enriches an existing friction
- replaces an outdated friction
- reveals a new structural limitation

Your objective is NOT to summarize today's observations.

Your objective is to identify the durable constraints that limit this entity's ability to execute its strategy, strengthen its position or achieve its objectives.

--------------------------------------------------
RULES

Every note must describe one durable friction specific to this entity.

Focus on limitations such as:

- competitive disadvantages
- business model constraints
- operational complexity
- execution risks
- technology limitations
- regulatory exposure
- organizational constraints
- dependency on partners, suppliers or platforms
- adoption barriers
- monetization challenges
- scalability limitations

Describe what constrains this entity.

Do NOT describe generic market challenges unless they specifically affect this entity.

Do NOT describe industry trends.

Do NOT explain how the entity works.

Do NOT explain why the topic is strategically important.

Ignore temporary issues.

Ignore isolated announcements.

Ignore communication.

If an observation contains no durable friction for this entity, ignore it.

Merge similar frictions.

Rewrite existing notes when necessary.

Delete obsolete frictions.

Keep only durable knowledge.

Prefer a small number of high-value insights over many weak observations.

--------------------------------------------------
OUTPUT

Return the complete updated notebook.

Only bullet points.

Each bullet must describe one durable friction affecting this entity.

No introduction.

No conclusion.

No numbering.

No markdown.

No explanations.
""".strip()
