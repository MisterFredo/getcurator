from fastapi import (
    APIRouter,
    HTTPException,
    Request,
)

from core.feedback.models import (
    ContentFeedbackRequest,
    ContentFeedbackResponse,
    DigestFeedbackConfirmationRequest,
    DigestFeedbackPreview,
)

from core.feedback.service import (
    get_current_content_feedback,
    record_content_feedback,
    remove_content_feedback,
)

from core.feedback.token_service import (
    DigestFeedbackTokenError,
    DigestFeedbackTokenExpiredError,
    verify_digest_feedback_token,
)

from core.expertise.content_service import (
    load_contents_by_ids,
)

from core.user.user_service import (
    get_user_by_id,
)

from utils.auth import (
    get_user_id_from_request,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter()


# ============================================================
# AUTHENTICATION
# ============================================================

def _require_user_id(
    request: Request,
) -> str:

    user_id = get_user_id_from_request(
        request
    )

    if not user_id:

        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    return user_id


# ============================================================
# TOKEN VALIDATION
# ============================================================

def _verify_digest_token(
    token: str,
):

    try:

        return (
            verify_digest_feedback_token(
                token
            )
        )

    except (
        DigestFeedbackTokenExpiredError
    ) as exc:

        raise HTTPException(
            status_code=410,
            detail=(
                "This feedback link has expired"
            ),
        ) from exc

    except DigestFeedbackTokenError as exc:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid feedback link"
            ),
        ) from exc

    except RuntimeError as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Feedback service is not configured"
            ),
        ) from exc


# ============================================================
# USER LANGUAGE
# ============================================================

def _get_user_language(
    user_id: str,
) -> str:

    user = get_user_by_id(
        user_id
    )

    if not user:

        return "fr"

    language = (
        user.get(
            "LANGUAGE"
        )
        or user.get(
            "language"
        )
        or "fr"
    )

    language = str(
        language
    ).lower()

    if language not in {
        "fr",
        "en",
    }:

        return "fr"

    return language


# ============================================================
# LOAD CONTENT TITLE
# ============================================================

def _load_content_title(
    content_id: str,
    language: str,
) -> str:

    contents = load_contents_by_ids(
        content_ids=[
            content_id,
        ],
        language=language,
    )

    if not contents:

        raise HTTPException(
            status_code=404,
            detail="Content not found",
        )

    return contents[0].title


# ============================================================
# RECORD AUTHENTICATED FEEDBACK
# ============================================================

@router.post(
    "/",
    response_model=ContentFeedbackResponse,
)
def create_content_feedback(
    payload: ContentFeedbackRequest,
    request: Request,
):

    user_id = _require_user_id(
        request
    )

    try:

        return record_content_feedback(

            user_id=user_id,

            content_id=(
                payload.content_id
            ),

            digest_id=(
                payload.digest_id
            ),

            feedback_type=(
                payload.feedback_type
            ),

            feedback_reason=(
                payload.feedback_reason
            ),

            # An authenticated endpoint is currently
            # used from the content drawer only.
            source="CONTENT_DRAWER",

        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(
                exc
            ),
        ) from exc


# ============================================================
# GET CURRENT AUTHENTICATED FEEDBACK
# ============================================================

@router.get(
    "/current/{content_id}",
)
def read_current_content_feedback(
    content_id: str,
    request: Request,
):

    user_id = _require_user_id(
        request
    )

    try:

        feedback = (
            get_current_content_feedback(
                user_id=user_id,
                content_id=content_id,
            )
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(
                exc
            ),
        ) from exc

    if (
        not feedback
        or not feedback.is_active
    ):

        return {
            "feedback": None,
        }

    return {
        "feedback":
            feedback.model_dump(),
    }


# ============================================================
# REMOVE AUTHENTICATED FEEDBACK
# ============================================================

@router.delete(
    "/current/{content_id}",
    response_model=ContentFeedbackResponse,
)
def delete_current_content_feedback(
    content_id: str,
    request: Request,
):

    user_id = _require_user_id(
        request
    )

    try:

        return remove_content_feedback(

            user_id=user_id,

            content_id=content_id,

            source="CONTENT_DRAWER",

        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(
                exc
            ),
        ) from exc


# ============================================================
# DIGEST FEEDBACK PREVIEW
# ============================================================

@router.get(
    "/digest/{token}",
    response_model=DigestFeedbackPreview,
)
def preview_digest_feedback(
    token: str,
):

    token_payload = (
        _verify_digest_token(
            token
        )
    )

    language = _get_user_language(
        token_payload.user_id
    )

    content_title = (
        _load_content_title(
            content_id=(
                token_payload.content_id
            ),
            language=language,
        )
    )

    current_feedback = (
        get_current_content_feedback(

            user_id=(
                token_payload.user_id
            ),

            content_id=(
                token_payload.content_id
            ),

        )
    )

    already_recorded = bool(

        current_feedback

        and current_feedback.is_active

        and (
            current_feedback.feedback_type
            == "NOT_RELEVANT"
        )

    )

    return DigestFeedbackPreview(

        token=token,

        digest_id=(
            token_payload.digest_id
        ),

        content_id=(
            token_payload.content_id
        ),

        content_title=content_title,
        language=language,

        feedback_type="NOT_RELEVANT",

        already_recorded=(
            already_recorded
        ),

    )


# ============================================================
# CONFIRM DIGEST FEEDBACK
# ============================================================

@router.post(
    "/digest/confirm",
    response_model=ContentFeedbackResponse,
)
def confirm_digest_feedback(
    payload: (
        DigestFeedbackConfirmationRequest
    ),
):

    token_payload = (
        _verify_digest_token(
            payload.token
        )
    )

    try:

        return record_content_feedback(

            user_id=(
                token_payload.user_id
            ),

            digest_id=(
                token_payload.digest_id
            ),

            content_id=(
                token_payload.content_id
            ),

            feedback_type=(
                token_payload.feedback_type
            ),

            feedback_reason=(
                payload.feedback_reason
            ),

            source="DIGEST",

        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(
                exc
            ),
        ) from exc


# ============================================================
# UNDO DIGEST FEEDBACK
# ============================================================

@router.post(
    "/digest/undo",
    response_model=ContentFeedbackResponse,
)
def undo_digest_feedback(
    payload: (
        DigestFeedbackConfirmationRequest
    ),
):

    token_payload = (
        _verify_digest_token(
            payload.token
        )
    )

    try:

        return remove_content_feedback(

            user_id=(
                token_payload.user_id
            ),

            digest_id=(
                token_payload.digest_id
            ),

            content_id=(
                token_payload.content_id
            ),

            source="DIGEST",

        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(
                exc
            ),
        ) from exc
