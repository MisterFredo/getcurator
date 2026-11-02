from typing import Literal
from pydantic import BaseModel, Field

class LibraryEditorialDecision(BaseModel):
    editorial_status: Literal['REVIEW', 'SELECTED', 'IGNORED']

class LibraryQualityDecision(BaseModel):
    topic_id: str = Field(min_length=1)
    quality_status: Literal['ACCEPTED', 'REJECTED']
    quality_reason: str | None = None

class LibraryQualityRequest(BaseModel):
    decisions: list[LibraryQualityDecision]
