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

    answer = run_llm(
        prompt=prompt,
        temperature=0.2,
    )

    # ========================================================
    # RESPONSE
    # ========================================================

    return ConversationResponse(
        interlocutor_id=request.interlocutor_id,
        answer=answer,
    )
