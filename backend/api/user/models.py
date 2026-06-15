from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List


SUPPORTED_LANGS = ["fr", "en"]


# =========================================================
# CREATE USER
# =========================================================

class CreateUserPayload(BaseModel):
    email: EmailStr
    password: str

    name: Optional[str] = None
    company: Optional[str] = None
    language: Optional[str] = "fr"

    universes: List[str] = Field(default_factory=list)

    role: Optional[str] = "user"

    @validator("language", pre=True, always=True)
    def validate_language(cls, v):
        if v not in SUPPORTED_LANGS:
            return "fr"
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

    name: Optional[str] = None
    company: Optional[str] = None
    language: Optional[str] = "fr"

    universes: List[str] = Field(default_factory=list)

    role: Optional[str] = None

    @validator("language", pre=True, always=True)
    def validate_language(cls, v):
        if v not in SUPPORTED_LANGS:
            return "fr"
        return v


# =========================================================
# ASSIGN UNIVERS
# =========================================================

class AssignUniversePayload(BaseModel):
    user_id: str
    universes: List[str] = Field(default_factory=list)

class UserKeywordPayload(BaseModel):
    keyword: str

class UserProfilePayload(BaseModel):

    geography_1: Optional[str] = None
    geography_2: Optional[str] = None
    geography_3: Optional[str] = None

    profile_text: Optional[str] = None
