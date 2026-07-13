from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ============================================================
# CREATE
# ============================================================

class ConceptCreate(BaseModel):

    label: str = Field(
        ...,
        min_length=1,
    )

    description: Optional[str] = None

    class Config:
        extra = "forbid"


# ============================================================
# UPDATE
# ============================================================

class ConceptUpdate(BaseModel):

    label: Optional[str] = None

    description: Optional[str] = None

    is_active: Optional[bool] = None

    class Config:
        extra = "forbid"


# ============================================================
# OUT
# ============================================================

class ConceptOut(BaseModel):

    id_concept: str

    label: str

    description: Optional[str] = None

    is_active: bool = True

    created_at: Optional[datetime] = None

    updated_at: Optional[datetime] = None

    class Config:
        extra = "forbid"
