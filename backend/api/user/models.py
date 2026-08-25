from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    validator,
)

from typing import (
    Optional,
    List,
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


# =========================================================
# CREATE USER
# =========================================================

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


# =========================================================
# USER PREFERENCES
# =========================================================

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


# =========================================================
# LOGIN
# =========================================================

class LoginPayload(
    BaseModel,
):

    email: EmailStr

    password: str


# =========================================================
# UPDATE USER
# =========================================================

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


# =========================================================
# ASSIGN UNIVERSES
# =========================================================

class AssignUniversePayload(
    BaseModel,
):

    user_id: str

    universes: List[str] = Field(
        default_factory=list,
    )


# =========================================================
# USER KEYWORD
# =========================================================

class UserKeywordPayload(
    BaseModel,
):

    user_id: Optional[str] = None

    keyword: str


# =========================================================
# USER PROFILE
# =========================================================

class UserProfilePayload(
    BaseModel,
):

    user_id: Optional[str] = None

    geography_1: Optional[str] = None

    geography_2: Optional[str] = None

    geography_3: Optional[str] = None

    profile_text: Optional[str] = None
