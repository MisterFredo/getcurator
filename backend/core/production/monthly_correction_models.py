from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class MonthlyCorrectionProposalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID
    document_artifact_id: UUID
    review_artifact_id: UUID
    corpus_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    context_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
