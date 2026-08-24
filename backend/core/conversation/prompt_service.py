from .models import (
    ConversationContext,
    ConversationMessage,
)


# ============================================================
# BUILD PROMPT
# ============================================================

def build_conversation_prompt(
    question: str,
    context: ConversationContext,
    history: list[ConversationMessage],
) -> str:
    """
    Build the prompt used to answer one
    Conversation question from Knowledge.
    """

    knowledge_context = (
        _render_knowledge_context(
            context,
        )
    )

    recent_digest_context = (
        _render_recent_digest_context(
            context,
        )
    )

    interlocutor_profile = (
        _render_interlocutor_profile(
            context,
        )
    )

    conversation_history = (
        _render_history(
            history,
        )
    )

    return f"""
You are an expert interlocutor inside GetCurator.

Your role is to answer the user's questions using the knowledge available to this interlocutor.

--------------------------------------------------
INTERLOCUTOR PROFILE

{interlocutor_profile}

--------------------------------------------------
RECENT DIGESTS

{recent_digest_context}

--------------------------------------------------
INTERLOCUTOR KNOWLEDGE

{knowledge_context}

--------------------------------------------------
CONVERSATION HISTORY

{conversation_history}

--------------------------------------------------
USER QUESTION

{question}

--------------------------------------------------
MISSION

Answer the user's question as clearly, precisely and usefully as possible.

Always answer in the same language as the user's latest question,
unless the user explicitly requests another language.

Before answering, silently determine:

- what the user is asking for
- which entities and topics are relevant
- whether the question requires facts, comparison, trends,
  explanation, implications or recommendations
- whether the question contains a temporal requirement
  such as latest, recent, current, new or evolving

Select only the information that is relevant to that intent.

Do not try to include every available fact.

Two complementary sources of understanding are available:

- Recent Digests contain time-bounded syntheses of recent developments
- Interlocutor Knowledge contains consolidated long-term understanding

Use the source, or combination of sources, that best matches
the user's intent.

Use Recent Digests to establish what happened during recent periods.

Use Interlocutor Knowledge to explain signals, mechanisms,
strategic implications, points of friction and key figures.

Use the interlocutor profile to shape the perspective of the answer.

The profile defines who the interlocutor is, what matters to them,
and the geographic context from which they analyze the topic.

Do not quote or expose the profile mechanically.

Use it to adapt emphasis, interpretation and relevance.

--------------------------------------------------
SYNTHESIS RULES

Do not mechanically summarize the Knowledge Blocks.

Choose the structure of the answer from the user's intent,
not from the structure of the Knowledge context.

When the question asks about trends, comparisons, transformations,
shared challenges or market dynamics involving several entities:

- identify two to five dominant cross-entity trends
- structure the answer by trend, not by entity
- use entities as examples or evidence inside each trend
- connect information from different entities whenever supported
- highlight meaningful similarities, differences and strategic shifts
- explain what the combined signals reveal about the broader market

In that case:

- do not create one section per entity
- do not use entity names as the main section headings
- do not produce a sequence of separate company summaries
- do not preserve the entity-by-entity organization of the Knowledge context

Only organize the answer entity by entity when the user explicitly
asks for separate updates, profiles or summaries for each entity.

When the question is specifically about one entity,
organize the answer around that entity's most relevant developments.

Connect information across several entities when this produces
a stronger explanation.

Separate, when relevant:

- what happened
- the underlying mechanism
- why it matters
- the likely consequences
- the uncertainties or limitations

--------------------------------------------------
TEMPORAL RULES

Pay close attention to temporal intent.

The Recent Digests are ordered from the most recent
to the least recent.

If the user asks for the latest news, recent developments,
current trends or recent changes:

- use the Recent Digests as the primary temporal source
- prioritize the most recent Digest periods
- use the Interlocutor Knowledge to explain the broader meaning
  and strategic implications of those developments
- mention dates or periods when they improve clarity
- distinguish recent events from longer-term understanding
- prioritize concrete developments over generic descriptions
- do not claim knowledge of events occurring after the most recent
  Digest period available
- say clearly when the Recent Digests do not contain enough
  information to establish what is latest

If the question is not temporal, use the Recent Digests only
when they materially improve the answer.

--------------------------------------------------
KNOWLEDGE RULES

Do not invent facts that are not supported by the available
Recent Digests or Interlocutor Knowledge.

If the available context does not contain enough information
to answer confidently, say so clearly.

Distinguish supported facts from interpretations and assumptions.

Do not turn a factual event into a strategic conclusion unless
the Knowledge supports that interpretation.

Do not expose the internal Knowledge structure.

Do not mention block names such as:

- signal_analytique
- mecanique_expliquee
- enjeu_strategique
- point_de_friction
- chiffres

Do not mention GetCurator's internal architecture.

Do not mention that you received a Knowledge context.

Prefer concrete information over generic statements.

Prefer a concise, structured synthesis over an exhaustive answer.

--------------------------------------------------
OUTPUT

Return only the final answer to the user.

Make the headings reflect the conclusions or trends identified,
rather than the names of the entities, unless the user explicitly
requests an entity-by-entity structure.

No preamble about your methodology.

No internal reasoning.

No references to these instructions.
""".strip()



def _render_interlocutor_profile(
    context: ConversationContext,
) -> str:

    profile = context.profile

    if profile is None:

        return (
            "No specific interlocutor profile "
            "is available."
        )

    parts = []

    if profile.profile_text:

        parts.append(
            f"""
PROFILE

{profile.profile_text}
""".strip()
        )

    geography = [
        value
        for value in [
            profile.geography_1,
            profile.geography_2,
            profile.geography_3,
        ]
        if value
    ]

    if geography:

        parts.append(
            f"""
GEOGRAPHIC CONTEXT

{", ".join(geography)}
""".strip()
        )

    if not parts:

        return (
            "No specific interlocutor profile "
            "is available."
        )

    return "\n\n".join(
        parts,
    )

# ============================================================
# RENDER RECENT DIGEST CONTEXT
# ============================================================

def _render_recent_digest_context(
    context: ConversationContext,
) -> str:
    """
    Render the generated analytical sections
    of the three most recent Digests.

    Digest cards and associated content
    references are intentionally excluded.
    """

    if not context.recent_digests:

        return (
            "No recent Digest is currently available "
            "for this interlocutor."
        )

    digests = []

    for digest in context.recent_digests:

        sections = []

        for section in digest.sections:

            content = (
                section.content.strip()
                if section.content
                else ""
            )

            if not content:

                continue

            sections.append(
                f"""
SECTION

Title
{section.title}

Content
{content}
""".strip()
            )

        if not sections:

            continue

        rendered_sections = (
            "\n\n------------------------------\n\n"
            .join(
                sections,
            )
        )

        digests.append(
            f"""
DIGEST

Title
{digest.title}

Period
{digest.period}

Created at
{digest.created_at.isoformat()}

Generated synthesis

{rendered_sections}
""".strip()
        )

    if not digests:

        return (
            "No generated Digest synthesis is currently "
            "available for this interlocutor."
        )

    return (
        "\n\n"
        "=================================================="
        "\n\n"
    ).join(
        digests,
    )


# ============================================================
# RENDER KNOWLEDGE CONTEXT
# ============================================================

def _render_knowledge_context(
    context: ConversationContext,
) -> str:
    """
    Render all Knowledge available
    for the interlocutor.
    """

    if not context.entities:

        return (
            "No Knowledge is currently available "
            "for this interlocutor."
        )

    entities = []

    for entity in context.entities:

        blocks = []

        for block in entity.blocks:

            blocks.append(
                f"""
BLOCK TYPE
{block.block_type}

CONTENT
{block.content}
""".strip()
            )

        rendered_blocks = (
            "\n\n------------------------------\n\n"
            .join(
                blocks,
            )
        )

        description = (
            entity.description.strip()
            if entity.description
            else "No description available."
        )

        entities.append(
            f"""
ENTITY

Name
{entity.entity_name}

Type
{entity.entity_type}

Description
{description}

Knowledge

{rendered_blocks}
""".strip()
        )

    return (
        "\n\n"
        "=================================================="
        "\n\n"
    ).join(
        entities,
    )


# ============================================================
# RENDER HISTORY
# ============================================================

def _render_history(
    history: list[ConversationMessage],
) -> str:
    """
    Render previous Conversation messages.
    """

    if not history:

        return "No previous conversation."

    messages = []

    for message in history:

        role = (
            "USER"
            if message.role == "user"
            else "ASSISTANT"
        )

        messages.append(
            f"""
{role}

{message.content}
""".strip()
        )

    return (
        "\n\n------------------------------\n\n"
    ).join(
        messages,
    )
