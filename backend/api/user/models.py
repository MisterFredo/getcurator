from datetime import (
    datetime,
)

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    validator,
)

from typing import (
    Any,
    Dict,
    List,
    Literal,
    Optional,
)


# ============================================================
# CONFIGURATION
# ============================================================

SUPPORTED_LANGS = [
    "fr",
    "en",
]

SUPPORTED_PROFILE_TYPES = [
    "USER",
    "EXPERT",
]


# ============================================================
# TYPES
# ============================================================

ProfileGenerationStatus = Literal[
    "BUILDING",
    "READY",
    "STALE",
    "ERROR",
]


# ============================================================
# CREATE USER
# ============================================================

class CreateUserPayload(
    BaseModel,
):

    email: EmailStr

    password: str

    name: Optional[str] = None

    company: Optional[str] = None

    language: Optional[str] = "fr"

    universes: Optional[List[str]] = None

    role: Optional[str] = "user"

    profile_type: Optional[str] = "USER"

    display_name: Optional[str] = None

    description: Optional[str] = None

    is_active: Optional[bool] = True


    @validator(
        "language",
        pre=True,
        always=True,
    )
    def validate_language(
        cls,
        value,
    ):

        if value not in SUPPORTED_LANGS:

            return "fr"

        return value


    @validator(
        "profile_type",
        pre=True,
        always=True,
    )
    def validate_profile_type(
        cls,
        value,
    ):

        if value not in SUPPORTED_PROFILE_TYPES:

            return "USER"

        return value


# ============================================================
# USER PREFERENCES
# ============================================================

class UserPreferencesPayload(
    BaseModel,
):

    user_id: str

    companies: list[str] = Field(
        default_factory=list,
    )

    solutions: list[str] = Field(
        default_factory=list,
    )

    topics: list[str] = Field(
        default_factory=list,
    )


# ============================================================
# LOGIN
# ============================================================

class LoginPayload(
    BaseModel,
):

    email: EmailStr

    password: str


# ============================================================
# UPDATE USER
# ============================================================

class UpdateUserPayload(
    BaseModel,
):

    user_id: str

    email: Optional[EmailStr] = None

    password: Optional[str] = None

    name: Optional[str] = None

    company: Optional[str] = None

    language: Optional[str] = "fr"

    universes: Optional[List[str]] = None

    role: Optional[str] = None

    profile_type: Optional[str] = None

    display_name: Optional[str] = None

    description: Optional[str] = None

    is_active: Optional[bool] = None


    @validator(
        "language",
        pre=True,
        always=True,
    )
    def validate_language(
        cls,
        value,
    ):

        if value not in SUPPORTED_LANGS:

            return "fr"

        return value


    @validator(
        "profile_type",
    )
    def validate_profile_type(
        cls,
        value,
    ):

        if value is None:

            return value

        if value not in SUPPORTED_PROFILE_TYPES:

            raise ValueError(
                "Invalid profile_type"
            )

        return value


# ============================================================
# ASSIGN UNIVERSES
# ============================================================

class AssignUniversePayload(
    BaseModel,
):

    user_id: str

    universes: List[str] = Field(
        default_factory=list,
    )


# ============================================================
# USER KEYWORD
# ============================================================

class UserKeywordPayload(
    BaseModel,
):

    user_id: Optional[str] = None

    keyword: str


# ============================================================
# USER PROFILE PAYLOAD
# ============================================================

class UserProfilePayload(
    BaseModel,
):
    """
    Public human-readable profile payload.

    This payload must never expose or accept the internal
    editorial profile.
    """

    user_id: Optional[str] = None

    geography_1: Optional[str] = None

    geography_2: Optional[str] = None

    geography_3: Optional[str] = None

    profile_text: Optional[str] = None


# ============================================================
# PUBLIC USER PROFILE RESPONSE
# ============================================================

class UserProfileResponse(
    BaseModel,
):
    """
    Profile representation allowed on the public front.
    """

    user_id: Optional[str] = None

    geography_1: Optional[str] = None

    geography_2: Optional[str] = None

    geography_3: Optional[str] = None

    profile_text: Optional[str] = None


# ============================================================
# ADMIN USER PROFILE RESPONSE
# ============================================================

class UserProfileAdminResponse(
    BaseModel,
):
    """
    Complete profile representation reserved for admin use.
    """

    user_id: str

    geography_1: Optional[str] = None

    geography_2: Optional[str] = None

    geography_3: Optional[str] = None

    # Public human-readable profile.
    profile_text: Optional[str] = None

    # Internal editorial profile.
    profile_editorial_text: Optional[str] = None

    profile_editorial_source_hash: Optional[str] = None

    profile_editorial_transformer_version: Optional[str] = None

    profile_editorial_at: Optional[datetime] = None

    profile_editorial_status: Optional[
        ProfileGenerationStatus
    ] = None

    profile_editorial_error: Optional[str] = None

    # Structured machine profile.
    structured_profile: Optional[
        Dict[str, Any]
    ] = None

    profile_source_hash: Optional[str] = None

    profile_schema_version: Optional[str] = None

    profile_transformer_version: Optional[str] = None

    profile_structured_at: Optional[datetime] = None

    profile_structured_status: Optional[
        ProfileGenerationStatus
    ] = None

    profile_structured_error: Optional[str] = None


# ============================================================
# ADMIN EDITORIAL PROFILE PAYLOAD
# ============================================================

class UserEditorialProfilePayload(
    BaseModel,
):
    """
    Manual editorial-profile update from the admin.

    This payload must not be exposed through public profile
    update routes.
    """

    user_id: str

    profile_editorial_text: str = Field(
        ...,
        min_length=1,
    )


# ============================================================
# PROFILE ASSISTANT MESSAGE
# ============================================================

class ProfileAssistantMessage(
    BaseModel,
):

    role: Literal[
        "user",
        "assistant",
    ]

    content: str = Field(
        ...,
        min_length=1,
        max_length=5000,
    )


# ============================================================
# PROFILE ASSISTANT PAYLOAD
# ============================================================

class UserProfileAssistantPayload(
    BaseModel,
):

    user_id: Optional[str] = None

    messages: List[
        ProfileAssistantMessage
    ] = Field(
        default_factory=list,
        max_items=12,
    )


# ============================================================
# PROFILE REGENERATE
# ============================================================

class UserProfileRegeneratePayload(
    BaseModel,
):

    user_id: Optional[str] = None

    force: bool = True
