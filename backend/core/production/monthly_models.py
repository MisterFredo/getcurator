from datetime import date
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class MonthlyStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID
    user_id: UUID
    month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    language: Literal["fr", "en"] = "en"
    allow_incomplete: bool = False
    new_version: bool = False


class MonthlyRefreshRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    response_id: str | None = Field(default=None, pattern=r"^resp_[A-Za-z0-9_]+$", max_length=200)


class MonthlyReviewIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Literal["PERIOD", "CHRONOLOGY", "NUMBER", "SCOPE", "COMPARISON", "REPETITION", "PROFILE", "CITATION"]
    location: str
    message: str


class MonthlyQualityReview(BaseModel):
    model_config = ConfigDict(extra="forbid")
    passed: bool
    issues: list[MonthlyReviewIssue] = Field(max_length=20)
