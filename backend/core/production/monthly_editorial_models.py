"""Explicit, version-bound admin text corrections."""
from typing import Annotated
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


SourceId = Annotated[str, Field(min_length=1, max_length=40)]
EvidenceIds = Annotated[list[SourceId], Field(min_length=1, max_length=100)]


class MonthlyEditorialEditRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID
    document_artifact_id: UUID
    review_artifact_id: UUID
    corpus_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    context_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    replacements: dict[str, Annotated[str, Field(min_length=1, max_length=2200)]] = Field(min_length=1, max_length=8)
    evidence_bindings: dict[str, EvidenceIds] = Field(min_length=1, max_length=8)
    reason: str = Field(min_length=1, max_length=2000)

    @field_validator("reason")
    @classmethod
    def nonempty_reason(cls, value):
        if not value.strip():
            raise ValueError("Le motif de correction est requis.")
        return value.strip()
