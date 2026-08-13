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
        interlocutor_id=request.interlocutor_id,
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

    answer = _generate_answer(
        prompt=prompt,
    )

    # ========================================================
    # RESPONSE
    # ========================================================

    return ConversationResponse(
        interlocutor_id=request.interlocutor_id,
        answer=answer,
    )


# ============================================================
# GENERATE ANSWER
# ============================================================

def _generate_answer(
    prompt: str,
) -> str:
    """
    Generate the final Conversation answer.

    This function must use the existing
    GetCurator LLM infrastructure.
    """

    raise NotImplementedError(
        "Conversation LLM adapter is not connected yet."
    )
