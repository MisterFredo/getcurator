from typing import (
    Optional,
)

from uuid import uuid4

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
)

from core.feedback.models import (
    ContentFeedback,
    ContentFeedbackReason,
    ContentFeedbackResponse,
    ContentFeedbackSource,
    ContentFeedbackType,
)


# ============================================================
# TABLE
# ============================================================

TABLE_USER_CONTENT_FEEDBACK = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_USER_CONTENT_FEEDBACK"
)


# ============================================================
# NORMALIZATION
# ============================================================

def _clean_required_id(
    value: str,
    field_name: str,
) -> str:

    cleaned_value = (
        value.strip()
        if isinstance(
            value,
            str,
        )
        else ""
    )

    if not cleaned_value:

        raise ValueError(
            f"{field_name} is required"
        )

    return cleaned_value


def _clean_optional_id(
    value: Optional[str],
) -> Optional[str]:

    if not isinstance(
        value,
        str,
    ):

        return None

    cleaned_value = value.strip()

    return (
        cleaned_value
        or None
    )


# ============================================================
# BUILD FEEDBACK FROM ROW
# ============================================================

def _build_feedback_from_row(
    row: dict,
) -> ContentFeedback:

    return ContentFeedback(

        id=row.get(
            "ID"
        ),

        user_id=row.get(
            "ID_USER"
        ),

        digest_id=row.get(
            "DIGEST_ID"
        ),

        content_id=row.get(
            "CONTENT_ID"
        ),

        feedback_type=row.get(
            "FEEDBACK_TYPE"
        ),

        feedback_reason=row.get(
            "FEEDBACK_REASON"
        ),

        source=row.get(
            "SOURCE"
        ),

        is_active=bool(
            row.get(
                "IS_ACTIVE"
            )
        ),

    )


# ============================================================
# GET CURRENT FEEDBACK
# ============================================================

def get_current_content_feedback(
    user_id: str,
    content_id: str,
) -> Optional[ContentFeedback]:

    cleaned_user_id = (
        _clean_required_id(
            user_id,
            "user_id",
        )
    )

    cleaned_content_id = (
        _clean_required_id(
            content_id,
            "content_id",
        )
    )

    rows = query_bq(
        f"""
        SELECT

            ID,
            ID_USER,
            DIGEST_ID,
            CONTENT_ID,
            FEEDBACK_TYPE,
            FEEDBACK_REASON,
            SOURCE,
            IS_ACTIVE,
            CREATED_AT,
            UPDATED_AT

        FROM `{TABLE_USER_CONTENT_FEEDBACK}`

        WHERE

            ID_USER = @user_id

            AND CONTENT_ID = @content_id

        QUALIFY

            ROW_NUMBER() OVER (

                PARTITION BY
                    ID_USER,
                    CONTENT_ID

                ORDER BY
                    UPDATED_AT DESC,
                    CREATED_AT DESC,
                    ID DESC

            ) = 1

        LIMIT 1
        """,
        {
            "user_id":
                cleaned_user_id,

            "content_id":
                cleaned_content_id,
        },
    )

    if not rows:

        return None

    return _build_feedback_from_row(
        rows[0]
    )


# ============================================================
# LIST CURRENT FEEDBACKS
# ============================================================

def list_current_content_feedbacks(
    user_id: str,
    active_only: bool = True,
) -> list[ContentFeedback]:

    cleaned_user_id = (
        _clean_required_id(
            user_id,
            "user_id",
        )
    )

    rows = query_bq(
        f"""
        WITH current_feedback AS (

            SELECT

                ID,
                ID_USER,
                DIGEST_ID,
                CONTENT_ID,
                FEEDBACK_TYPE,
                FEEDBACK_REASON,
                SOURCE,
                IS_ACTIVE,
                CREATED_AT,
                UPDATED_AT

            FROM `{TABLE_USER_CONTENT_FEEDBACK}`

            WHERE ID_USER = @user_id

            QUALIFY

                ROW_NUMBER() OVER (

                    PARTITION BY
                        ID_USER,
                        CONTENT_ID

                    ORDER BY
                        UPDATED_AT DESC,
                        CREATED_AT DESC,
                        ID DESC

                ) = 1

        )

        SELECT

            ID,
            ID_USER,
            DIGEST_ID,
            CONTENT_ID,
            FEEDBACK_TYPE,
            FEEDBACK_REASON,
            SOURCE,
            IS_ACTIVE,
            CREATED_AT,
            UPDATED_AT

        FROM current_feedback

        WHERE (

            @active_only = FALSE

            OR IS_ACTIVE = TRUE

        )

        ORDER BY UPDATED_AT DESC
        """,
        {
            "user_id":
                cleaned_user_id,

            "active_only":
                active_only,
        },
    )

    return [

        _build_feedback_from_row(
            row
        )

        for row in rows

    ]


# ============================================================
# INSERT FEEDBACK EVENT
# ============================================================

def _insert_feedback_event(
    user_id: str,
    content_id: str,
    feedback_type: ContentFeedbackType,
    source: ContentFeedbackSource,
    digest_id: Optional[str] = None,
    feedback_reason: Optional[
        ContentFeedbackReason
    ] = None,
    is_active: bool = True,
) -> str:

    feedback_id = str(
        uuid4()
    )

    query_bq(
        f"""
        INSERT INTO `{TABLE_USER_CONTENT_FEEDBACK}`
        (
            ID,
            ID_USER,
            DIGEST_ID,
            CONTENT_ID,
            FEEDBACK_TYPE,
            FEEDBACK_REASON,
            SOURCE,
            IS_ACTIVE,
            CREATED_AT,
            UPDATED_AT
        )

        VALUES
        (
            @feedback_id,
            @user_id,
            @digest_id,
            @content_id,
            @feedback_type,
            @feedback_reason,
            @source,
            @is_active,
            CURRENT_TIMESTAMP(),
            CURRENT_TIMESTAMP()
        )
        """,
        {
            "feedback_id":
                feedback_id,

            "user_id":
                user_id,

            "digest_id":
                digest_id,

            "content_id":
                content_id,

            "feedback_type":
                feedback_type,

            "feedback_reason":
                feedback_reason,

            "source":
                source,

            "is_active":
                is_active,
        },
    )

    return feedback_id


# ============================================================
# RECORD FEEDBACK
# ============================================================

def record_content_feedback(
    user_id: str,
    content_id: str,
    feedback_type: ContentFeedbackType,
    source: ContentFeedbackSource,
    digest_id: Optional[str] = None,
    feedback_reason: Optional[
        ContentFeedbackReason
    ] = None,
) -> ContentFeedbackResponse:

    cleaned_user_id = (
        _clean_required_id(
            user_id,
            "user_id",
        )
    )

    cleaned_content_id = (
        _clean_required_id(
            content_id,
            "content_id",
        )
    )

    cleaned_digest_id = (
        _clean_optional_id(
            digest_id
        )
    )

    # A positive signal does not need a rejection reason.
    if feedback_type == "RELEVANT":

        feedback_reason = None

    current_feedback = (
        get_current_content_feedback(
            user_id=cleaned_user_id,
            content_id=cleaned_content_id,
        )
    )

    # ========================================================
    # UNCHANGED
    # ========================================================

    if (
        current_feedback
        and current_feedback.is_active
        and (
            current_feedback.feedback_type
            == feedback_type
        )
        and (
            current_feedback.feedback_reason
            == feedback_reason
        )
    ):

        return ContentFeedbackResponse(

            status="unchanged",

            content_id=(
                cleaned_content_id
            ),

            feedback_type=(
                current_feedback
                .feedback_type
            ),

            feedback_reason=(
                current_feedback
                .feedback_reason
            ),

            source=(
                current_feedback
                .source
            ),

            is_active=True,

            message=(
                "Feedback already recorded"
            ),

        )

    status = (
        "updated"
        if current_feedback
        else "recorded"
    )

    _insert_feedback_event(

        user_id=cleaned_user_id,

        content_id=cleaned_content_id,

        digest_id=cleaned_digest_id,

        feedback_type=feedback_type,

        feedback_reason=feedback_reason,

        source=source,

        is_active=True,

    )

    return ContentFeedbackResponse(

        status=status,

        content_id=cleaned_content_id,

        feedback_type=feedback_type,

        feedback_reason=(
            feedback_reason
        ),

        source=source,

        is_active=True,

        message=(
            "Feedback recorded"
        ),

    )


# ============================================================
# REMOVE FEEDBACK
# ============================================================

def remove_content_feedback(
    user_id: str,
    content_id: str,
    source: Optional[
        ContentFeedbackSource
    ] = None,
    digest_id: Optional[str] = None,
) -> ContentFeedbackResponse:

    cleaned_user_id = (
        _clean_required_id(
            user_id,
            "user_id",
        )
    )

    cleaned_content_id = (
        _clean_required_id(
            content_id,
            "content_id",
        )
    )

    current_feedback = (
        get_current_content_feedback(
            user_id=cleaned_user_id,
            content_id=cleaned_content_id,
        )
    )

    if (
        not current_feedback
        or not current_feedback.is_active
    ):

        return ContentFeedbackResponse(

            status="unchanged",

            content_id=(
                cleaned_content_id
            ),

            feedback_type=None,

            feedback_reason=None,

            source=None,

            is_active=False,

            message=(
                "No active feedback to remove"
            ),

        )

    reset_source = (
        source
        or current_feedback.source
    )

    reset_digest_id = (
        _clean_optional_id(
            digest_id
        )
        or current_feedback.digest_id
    )

    _insert_feedback_event(

        user_id=cleaned_user_id,

        content_id=cleaned_content_id,

        digest_id=reset_digest_id,

        feedback_type=(
            current_feedback
            .feedback_type
        ),

        feedback_reason=(
            current_feedback
            .feedback_reason
        ),

        source=reset_source,

        is_active=False,

    )

    return ContentFeedbackResponse(

        status="removed",

        content_id=cleaned_content_id,

        feedback_type=None,

        feedback_reason=None,

        source=reset_source,

        is_active=False,

        message=(
            "Feedback removed"
        ),

    )
