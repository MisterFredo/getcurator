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

from utils.auth import (
    get_user_id_from_request,
)


router = APIRouter()


# ============================================================
# CONVERSE
# ============================================================

@router.post(
    "",
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

    question = (
        payload.question
        or ""
    ).strip()

    if not question:

        raise HTTPException(
            status_code=400,
            detail="Question is required",
        )

    if not payload.interlocutor_id:

        raise HTTPException(
            status_code=400,
            detail="Interlocutor is required",
        )

    # ========================================================
    # CONVERSATION
    # ========================================================

    try:

        return converse(
            payload,
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
