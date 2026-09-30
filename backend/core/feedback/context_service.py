from datetime import (
    datetime,
    timedelta,
    timezone,
)

from typing import (
    Any,
)

from core.feedback.models import (
    ContentFeedback,
    FeedbackContentExample,
    UserFeedbackContext,
)

from core.feedback.service import (
    list_current_content_feedbacks,
)

from core.expertise.content_service import (
    load_contents_by_ids,
)


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_FEEDBACK_LOOKBACK_DAYS = 90

DEFAULT_FEEDBACK_EXAMPLES_PER_TYPE = 8


# ============================================================
# NORMALIZE LABELS
# ============================================================

def _normalize_labels(
    values: Any,
    possible_keys: tuple[
        str,
        ...,
    ],
) -> list[str]:

    if not isinstance(
        values,
        list,
    ):

        return []

    labels: list[str] = []

    seen: set[str] = set()

    for value in values:

        label = None

        if isinstance(
            value,
            dict,
        ):

            for key in possible_keys:

                candidate = value.get(
                    key
                )

                if (
                    isinstance(
                        candidate,
                        str,
                    )
                    and candidate.strip()
                ):

                    label = candidate.strip()

                    break

        elif isinstance(
            value,
            str,
        ):

            label = value.strip()

        if not label:

            continue

        normalized_label = (
            label.casefold()
        )

        if normalized_label in seen:

            continue

        seen.add(
            normalized_label
        )

        labels.append(
            label
        )

    return labels


# ============================================================
# RECENT FEEDBACK
# ============================================================

def _is_recent_feedback(
    feedback: ContentFeedback,
    minimum_date: datetime,
) -> bool:

    feedback_at = (
        feedback.updated_at
        or feedback.created_at
    )

    if feedback_at is None:

        return True

    if feedback_at.tzinfo is None:

        feedback_at = feedback_at.replace(
            tzinfo=timezone.utc
        )

    return (
        feedback_at
        >= minimum_date
    )


# ============================================================
# BUILD EXAMPLE
# ============================================================

def _build_feedback_example(
    feedback: ContentFeedback,
    content,
) -> FeedbackContentExample:

    return FeedbackContentExample(

        content_id=(
            feedback.content_id
        ),

        title=(
            content.title
            or ""
        ),

        excerpt=(
            content.excerpt
            or ""
        ),

        feedback_type=(
            feedback.feedback_type
        ),

        feedback_reason=(
            feedback.feedback_reason
        ),

        source=(
            feedback.source
        ),

        feedback_at=(
            feedback.updated_at
            or feedback.created_at
        ),

        companies=(
            _normalize_labels(
                content.companies,
                (
                    "name",
                    "label",
                ),
            )
        ),

        solutions=(
            _normalize_labels(
                content.solutions,
                (
                    "name",
                    "label",
                ),
            )
        ),

        topics=(
            _normalize_labels(
                content.topics,
                (
                    "label",
                    "name",
                ),
            )
        ),

        concepts=(
            _normalize_labels(
                content.concepts,
                (
                    "label",
                    "name",
                ),
            )
        ),

    )


# ============================================================
# EMPTY CONTEXT
# ============================================================

def _empty_feedback_context(
) -> UserFeedbackContext:

    return UserFeedbackContext(

        relevant_examples=[],

        not_relevant_examples=[],

        relevant_count=0,

        not_relevant_count=0,

        has_feedback=False,

    )


# ============================================================
# BUILD USER FEEDBACK CONTEXT
# ============================================================

def build_user_feedback_context(
    user_id: str,
    language: str = "fr",
    lookback_days: int = (
        DEFAULT_FEEDBACK_LOOKBACK_DAYS
    ),
    examples_per_type: int = (
        DEFAULT_FEEDBACK_EXAMPLES_PER_TYPE
    ),
) -> UserFeedbackContext:
    """
    Build a compact behavioral context from the user's current
    explicit feedback.

    This context does not modify the user profile.

    It provides recent positive and negative examples to the
    Digest selection engine.
    """

    cleaned_user_id = (
        user_id.strip()
        if isinstance(
            user_id,
            str,
        )
        else ""
    )

    if not cleaned_user_id:

        return (
            _empty_feedback_context()
        )

    supported_language = (
        language
        if language in {
            "fr",
            "en",
        }
        else "fr"
    )

    minimum_date = (

        datetime.now(
            timezone.utc
        )

        - timedelta(
            days=max(
                1,
                lookback_days,
            )
        )

    )

    feedbacks = (
        list_current_content_feedbacks(

            user_id=cleaned_user_id,

            active_only=True,

        )
    )

    recent_feedbacks = [

        feedback

        for feedback in feedbacks

        if _is_recent_feedback(
            feedback=feedback,
            minimum_date=minimum_date,
        )

    ]

    if not recent_feedbacks:

        return (
            _empty_feedback_context()
        )

    content_ids = [

        feedback.content_id

        for feedback in recent_feedbacks

    ]

    contents = load_contents_by_ids(

        content_ids=content_ids,

        language=supported_language,

    )

    contents_by_id = {

        content.id:
            content

        for content in contents

    }

    relevant_examples: list[
        FeedbackContentExample
    ] = []

    not_relevant_examples: list[
        FeedbackContentExample
    ] = []

    relevant_count = 0

    not_relevant_count = 0

    maximum_examples = max(
        1,
        examples_per_type,
    )

    for feedback in recent_feedbacks:

        content = contents_by_id.get(
            feedback.content_id
        )

        if content is None:

            continue

        example = (
            _build_feedback_example(
                feedback=feedback,
                content=content,
            )
        )

        if (
            feedback.feedback_type
            == "RELEVANT"
        ):

            relevant_count += 1

            if (
                len(
                    relevant_examples
                )
                < maximum_examples
            ):

                relevant_examples.append(
                    example
                )

        elif (
            feedback.feedback_type
            == "NOT_RELEVANT"
        ):

            not_relevant_count += 1

            if (
                len(
                    not_relevant_examples
                )
                < maximum_examples
            ):

                not_relevant_examples.append(
                    example
                )

    return UserFeedbackContext(

        relevant_examples=(
            relevant_examples
        ),

        not_relevant_examples=(
            not_relevant_examples
        ),

        relevant_count=(
            relevant_count
        ),

        not_relevant_count=(
            not_relevant_count
        ),

        has_feedback=bool(
            relevant_examples
            or not_relevant_examples
        ),

    )
