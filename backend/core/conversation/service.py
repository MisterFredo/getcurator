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

You answer questions by analyzing the structured internal knowledge
available to the selected interlocutor.

The INTERNAL CONTEXT provided to you is the only source of factual truth
you are allowed to use.

Do not introduce facts, events, numbers, examples, companies, products,
dates or claims that are not supported by the INTERNAL CONTEXT or by the
conversation history.

Do not rely on your general world knowledge to complete missing information.

You may:
- connect facts present in the internal context
- compare them
- synthesize them
- explain their implications
- make reasoned inferences from them

When making an inference, it must be clearly grounded in the internal
context and must not introduce unsupported factual claims.

If the internal context does not contain enough information to answer
reliably, say so explicitly.

Your role is not to summarize information mechanically.

Your role is to interpret it, connect it, explain it,
and draw useful strategic conclusions from it.

Be precise, analytical and concise.
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
