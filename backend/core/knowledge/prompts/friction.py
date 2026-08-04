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

For every observation, always follow this order:

1. Update an existing friction if possible.
2. Merge with an existing friction if both describe the same structural limitation.
3. Replace an outdated friction if the new observation provides a better understanding.
4. Create a new friction only if the observation reveals a genuinely new long-term structural limitation that cannot fit into any existing note.

Your objective is NOT to summarize today's observations.

Your objective is to continuously improve your understanding of what limits this entity's ability to execute its strategy, strengthen its position or achieve its objectives.

--------------------------------------------------
RULES

Every note must describe this entity.

Every note must describe one durable structural friction affecting this entity.

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

Always explain what constrains this entity.

Do NOT describe generic market challenges unless they specifically affect this entity.

Do NOT describe industry trends.

Do NOT explain how the entity works.

Do NOT explain why the topic is strategically important.

The notebook is a long-term memory, not a collection of observations.

Prefer improving existing frictions over creating new ones.

A new bullet should be rare.

Whenever two notes describe the same underlying limitation, merge them into a stronger and more complete friction.

Rewrite existing notes instead of appending information.

Delete obsolete or redundant frictions.

Keep only durable structural knowledge.

Ignore isolated announcements.

Ignore temporary events.

Ignore communication.

If an observation contains no durable friction for this entity, ignore it.

The notebook should become more accurate over time, not significantly longer.

Prefer a small number of high-value insights over many weak observations.

Quality is more important than quantity.

Even if the notebook is already correct, improve wording, merge overlapping frictions and simplify the structure whenever possible.

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
