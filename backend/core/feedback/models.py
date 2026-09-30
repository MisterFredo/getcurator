from datetime import (
    datetime,
)

from typing import (
    Literal,
    Optional,
)

from pydantic import (
    BaseModel,
    Field,
)


# ============================================================
# TYPES
# ============================================================

ContentFeedbackType = Literal[
    "RELEVANT",
    "NOT_RELEVANT",
]

ContentFeedbackSource = Literal[
    "DIGEST",
    "CONTENT_DRAWER",
]

ContentFeedbackReason = Literal[
    "WRONG_TOPIC",
    "WRONG_MARKET",
    "WRONG_COMPANY",
    "TOO_GENERAL",
    "ALREADY_KNOWN",
    "OTHER",
]


# ============================================================
# EXPLICIT CONTENT FEEDBACK
# ============================================================

class ContentFeedback(
    BaseModel,
):

    id: str

    user_id: str

    content_id: str
    created_at: Optional[
        datetime
    ] = None

    updated_at: Optional[
        datetime
    ] = None

    digest_id: Optional[str] = None

    feedback_type: ContentFeedbackType

    feedback_reason: Optional[
        ContentFeedbackReason
    ] = None

    source: ContentFeedbackSource

    is_active: bool = True


# ============================================================
# AUTHENTICATED FEEDBACK REQUEST
# ============================================================

class ContentFeedbackRequest(
    BaseModel,
):
    """
    Explicit feedback submitted by an authenticated user.

    Used primarily from the content drawer.
    """

    content_id: str = Field(
        ...,
        min_length=1,
    )

    digest_id: Optional[str] = None

    feedback_type: ContentFeedbackType

    feedback_reason: Optional[
        ContentFeedbackReason
    ] = None

    source: ContentFeedbackSource = (
        "CONTENT_DRAWER"
    )


# ============================================================
# DIGEST FEEDBACK TOKEN PAYLOAD
# ============================================================

class DigestFeedbackTokenPayload(
    BaseModel,
):
    """
    Internal payload carried by the signed Digest feedback token.

    The token is verified by the backend before this payload
    may be used.
    """

    user_id: str

    digest_id: str

    content_id: str

    feedback_type: Literal[
        "NOT_RELEVANT",
    ] = "NOT_RELEVANT"


# ============================================================
# DIGEST FEEDBACK PREVIEW
# ============================================================

class DigestFeedbackPreview(
    BaseModel,
):

    token: str

    digest_id: str

    content_id: str

    content_title: str

    language: Literal[
        "fr",
        "en",
    ] = "en"

    feedback_type: Literal[
        "NOT_RELEVANT",
    ] = "NOT_RELEVANT"

    already_recorded: bool = False


# ============================================================
# DIGEST FEEDBACK CONFIRMATION
# ============================================================

class DigestFeedbackConfirmationRequest(
    BaseModel,
):
    """
    Confirmation submitted from the public Digest feedback page.

    The user and content identifiers are recovered from the
    verified token and are not accepted directly from the client.
    """

    token: str = Field(
        ...,
        min_length=1,
    )

    feedback_reason: Optional[
        ContentFeedbackReason
    ] = None


# ============================================================
# FEEDBACK RESET REQUEST
# ============================================================

class ContentFeedbackResetRequest(
    BaseModel,
):
    """
    Remove the current explicit feedback state.

    A reset creates an inactive historical event rather than
    deleting previous feedback.
    """

    content_id: Optional[str] = None

    token: Optional[str] = None


# ============================================================
# FEEDBACK RESPONSE
# ============================================================

class ContentFeedbackResponse(
    BaseModel,
):

    status: Literal[
        "recorded",
        "updated",
        "removed",
        "unchanged",
    ]

    content_id: str

    feedback_type: Optional[
        ContentFeedbackType
    ] = None

    feedback_reason: Optional[
        ContentFeedbackReason
    ] = None

    source: Optional[
        ContentFeedbackSource
    ] = None

    is_active: bool

    message: str

# ============================================================
# FEEDBACK CONTENT EXAMPLE
# ============================================================

class FeedbackContentExample(
    BaseModel,
):

    content_id: str

    title: str

    excerpt: str = ""

    feedback_type: ContentFeedbackType

    feedback_reason: Optional[
        ContentFeedbackReason
    ] = None

    source: ContentFeedbackSource

    feedback_at: Optional[
        datetime
    ] = None

    companies: list[str] = Field(
        default_factory=list,
    )

    solutions: list[str] = Field(
        default_factory=list,
    )

    topics: list[str] = Field(
        default_factory=list,
    )

    concepts: list[str] = Field(
        default_factory=list,
    )


# ============================================================
# USER FEEDBACK CONTEXT
# ============================================================

class UserFeedbackContext(
    BaseModel,
):

    relevant_examples: list[
        FeedbackContentExample
    ] = Field(
        default_factory=list,
    )

    not_relevant_examples: list[
        FeedbackContentExample
    ] = Field(
        default_factory=list,
    )

    relevant_count: int = 0

    not_relevant_count: int = 0

    has_feedback: bool = False
