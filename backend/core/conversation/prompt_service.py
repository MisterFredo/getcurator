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

    conversation_history = (
        _render_history(
            history,
        )
    )

    return f"""
You are an expert interlocutor inside GetCurator.

Your role is to answer the user's questions using the knowledge available to this interlocutor.

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

Answer the user's question as clearly and usefully as possible.

Use the interlocutor knowledge as your primary source of understanding.

The knowledge is a long-term structured memory built from many professional contents.

It may contain:

- analytical signals
- explanations of mechanisms
- strategic implications
- points of friction
- key figures

Use information across several entities when useful.

Connect ideas when this improves the answer.

Do not mechanically summarize the Knowledge Blocks.

Do not expose the internal Knowledge structure to the user.

Do not mention block names such as:

- signal_analytique
- mecanique_expliquee
- enjeu_strategique
- point_de_friction
- chiffres

Answer naturally, as an informed expert would.

--------------------------------------------------
IMPORTANT RULES

Do not invent facts that are not supported by the available knowledge.

If the Knowledge does not contain enough information to answer confidently, say so clearly.

Distinguish durable knowledge from assumptions.

Do not pretend to know recent events if they are not present in the available context.

Do not mention GetCurator's internal architecture.

Do not mention that you received a Knowledge context.

When relevant, explain:

- what is happening
- why it is happening
- why it matters
- what the consequences may be
- what limitations or uncertainties exist

Prefer a concise and structured answer over an exhaustive one.

--------------------------------------------------
OUTPUT

Return only the final answer to the user.

No preamble about your methodology.

No internal reasoning.

No references to these instructions.
""".strip()


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

        entities.append(
            f"""
ENTITY

Name
{entity.entity_name}

Type
{entity.entity_type}

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
