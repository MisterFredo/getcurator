from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List


SUPPORTED_LANGS = ["fr", "en"]

SUPPORTED_PROFILE_TYPES = [
    "USER",
    "EXPERT",
]

SUPPORTED_FREQUENCIES = [
    "WEEKLY",
    "MONTHLY",
]


# =========================================================
# CREATE USER
# =========================================================

class CreateUserPayload(BaseModel):
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
    frequency: Optional[str] = "WEEKLY"
    is_active: Optional[bool] = True

    @validator("language", pre=True, always=True)
    def validate_language(cls, v):
        if v not in SUPPORTED_LANGS:
            return "fr"
        return v

    @validator("profile_type", pre=True, always=True)
    def validate_profile_type(cls, v):
        if v not in SUPPORTED_PROFILE_TYPES:
            return "USER"
        return v

    @validator("frequency", pre=True, always=True)
    def validate_frequency(cls, v):
        if v not in SUPPORTED_FREQUENCIES:
            return "WEEKLY"
        return v


# =========================================================
# LOGIN
# =========================================================

class LoginPayload(BaseModel):
    email: EmailStr
    password: str


# =========================================================
# UPDATE USER
# =========================================================

class UpdateUserPayload(BaseModel):
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

    frequency: Optional[str] = None
    is_active: Optional[bool] = None

    @validator("language", pre=True, always=True)
    def validate_language(cls, v):
        if v not in SUPPORTED_LANGS:
            return "fr"
        return v

    @validator("profile_type")
    def validate_profile_type(cls, v):
        if v is None:
            return v
        if v not in SUPPORTED_PROFILE_TYPES:
            raise ValueError("Invalid profile_type")
        return v

    @validator("frequency")
    def validate_frequency(cls, v):
        if v is None:
            return v
        if v not in SUPPORTED_FREQUENCIES:
            raise ValueError("Invalid frequency")
        return v

# =========================================================
# ASSIGN UNIVERS
# =========================================================

class AssignUniversePayload(BaseModel):
    user_id: str
    universes: List[str] = Field(default_factory=list)


class UserKeywordPayload(BaseModel):

    user_id: Optional[str] = None
    keyword: str


class UserProfilePayload(BaseModel):

    user_id: Optional[str] = None

    geography_1: Optional[str] = None
    geography_2: Optional[str] = None
    geography_3: Optional[str] = None

    profile_text: Optional[str] = None
