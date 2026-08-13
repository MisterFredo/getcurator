from utils.llm import (
    run_llm,
)

from .models import (
    ConversationRequest,
    ConversationResponse,
)

from .context_service import (
    get_interlocutor_context,
)

from .prompt_service import (
    build_conversation_prompt,
)


# ============================================================
# SYSTEM PROMPT
# ============================================================

CONVERSATION_SYSTEM_PROMPT = """
You are a senior expert consultant.

You answer questions by analyzing the structured knowledge
available to the selected interlocutor.

Your role is not to summarize information mechanically.

Your role is to interpret it, connect it, explain it,
and draw useful strategic conclusions from it.

Be precise, analytical and concise.

Never invent facts that are not supported by the
available context.
""".strip()


# ============================================================
# CONVERSE
# ============================================================

def converse(
    request: ConversationRequest,
) -> ConversationResponse:
    """
    Answer one question for one interlocutor.
    """

    # ========================================================
    # CONTEXT
    # ========================================================

    context = get_interlocutor_context(
        interlocutor_id=
            request.interlocutor_id,
    )

    # ========================================================
    # PROMPT
    # ========================================================

    prompt = build_conversation_prompt(
        question=request.question,
        context=context,
        history=request.history,
    )

    # ========================================================
    # LLM
    # ========================================================

    answer = run_llm(
        prompt=prompt,
        temperature=0.2,
        system_prompt=
            CONVERSATION_SYSTEM_PROMPT,
    )

    # ========================================================
    # RESPONSE
    # ========================================================

    return ConversationResponse(
        interlocutor_id=
            request.interlocutor_id,

        answer=answer,
    )
