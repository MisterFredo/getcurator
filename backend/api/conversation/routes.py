from fastapi import (
    APIRouter,
    HTTPException,
    Request,
)

from core.conversation.models import (
    ConversationRequest,
    ConversationResponse,
)

from core.conversation.service import (
    converse,
)

from core.user.user_expert_service import (
    is_user_subscribed_to_expert,
)

from utils.auth import (
    get_user_id_from_request,
)


router = APIRouter()


# ============================================================
# CONVERSE
# ============================================================

@router.post(
    "/",
    response_model=ConversationResponse,
)
def converse_route(
    request: Request,
    payload: ConversationRequest,
):

    # ========================================================
    # AUTH
    # ========================================================

    user_id = get_user_id_from_request(
        request,
    )

    if not user_id:

        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    if not payload.interlocutor_id:

        raise HTTPException(
            status_code=400,
            detail="Interlocutor is required",
        )

    question = (
        payload.question
        or ""
    ).strip()

    if not question:

        raise HTTPException(
            status_code=400,
            detail="Question is required",
        )

    # ========================================================
    # INTERLOCUTOR ACCESS
    # ========================================================

    if payload.interlocutor_id != user_id:

        allowed = is_user_subscribed_to_expert(
            user_id=user_id,
            expert_id=payload.interlocutor_id,
        )

        if not allowed:

            raise HTTPException(
                status_code=403,
                detail="Interlocutor not available",
            )

    # ========================================================
    # CLEAN REQUEST
    # ========================================================

    clean_payload = payload.model_copy(
        update={
            "question": question,
        },
    )

    # ========================================================
    # CONVERSATION
    # ========================================================

    try:

        return converse(
            clean_payload,
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except Exception as e:

        print(
            "❌ Conversation error:",
            e,
        )

        raise HTTPException(
            status_code=500,
            detail="Conversation failed",
        )
