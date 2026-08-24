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

Select only the Knowledge that is relevant to that intent.

Do not try to include every available fact.

Use the interlocutor Knowledge as your primary source of understanding.

The Knowledge is a long-term structured memory built from many
professional contents. It may contain both durable understanding
and recent developments.

Use the interlocutor profile to shape the perspective of the answer.

The profile defines who the interlocutor is, what matters to them,
and the geographic context from which they analyze the topic.

Do not quote or expose the profile mechanically.

Use it to adapt emphasis, interpretation and relevance.

--------------------------------------------------
SYNTHESIS RULES

Do not mechanically summarize the Knowledge Blocks.

Do not automatically organize the answer entity by entity.

When the question asks about trends, comparisons, transformations,
shared challenges or market dynamics:

- identify the main cross-entity themes or mechanisms
- organize the answer around those themes
- use individual entities as supporting examples
- highlight meaningful similarities and differences
- explain what the combined signals reveal

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

If the user asks for the latest news, recent developments,
current trends or recent changes:

- prioritize the most recent facts available in the Knowledge
- mention dates or periods when they are available
- distinguish recent events from longer-term background
- do not describe old or undated information as recent
- prioritize concrete events over generic company descriptions
- say clearly when the available Knowledge is not sufficiently
  dated to establish what is latest

--------------------------------------------------
KNOWLEDGE RULES

Do not invent facts that are not supported by the available Knowledge.

If the Knowledge does not contain enough information to answer
confidently, say so clearly.

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
