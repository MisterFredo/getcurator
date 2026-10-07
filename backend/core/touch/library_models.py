from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class LibraryModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LibraryFilters(LibraryModel):
    expert_id: str | None = None
    month: str | None = Field(default=None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    output_language: Literal["fr", "en"] | None = None


class LibraryMessage(LibraryModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class LibrarySearchRequest(LibraryModel):
    message: str = Field(min_length=1, max_length=2000)
    history: list[LibraryMessage] = Field(default_factory=list, max_length=12)
    filters: LibraryFilters = Field(default_factory=LibraryFilters)
    language: Literal["fr", "en"] = "en"

    @field_validator("message")
    @classmethod
    def clean_message(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("La demande ne peut pas être vide.")
        return value


class LibrarySearchIntent(LibraryModel):
    action: Literal["SEARCH", "CLARIFY", "OUT_OF_SCOPE"]
    # AND between groups; OR between the bilingual variants of one concept.
    term_groups: list[list[str]] = Field(default_factory=list, max_length=6)
    exclusions: list[str] = Field(default_factory=list, max_length=6)
    month: str | None = Field(default=None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    clarification: str = Field(default="", max_length=300)

    @field_validator("term_groups")
    @classmethod
    def clean_groups(cls, groups):
        result = []
        for group in groups:
            cleaned = list(dict.fromkeys(term.strip() for term in group if term.strip()))
            if not cleaned or len(cleaned) > 5 or any(len(term) > 120 for term in cleaned):
                raise ValueError("Invalid search term group.")
            result.append(cleaned)
        return result


class LibraryMatch(LibraryModel):
    report_id: str
    match_type: Literal["DIRECT", "PARTIAL"]
    reason: str = Field(min_length=1, max_length=500)
    evidence_id: str


class LibraryRanking(LibraryModel):
    matches: list[LibraryMatch] = Field(default_factory=list, max_length=10)
