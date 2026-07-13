from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============================================================
# CREATE
# ============================================================

class SolutionCreate(BaseModel):

    name: str

    id_company: str

    description: Optional[str] = None

    content: Optional[str] = None

    aliases: List[str] = Field(default_factory=list)

    class Config:
        extra = "forbid"


# ============================================================
# UPDATE
# ============================================================

class SolutionUpdate(BaseModel):

    name: Optional[str] = None

    id_company: Optional[str] = None

    description: Optional[str] = None

    content: Optional[str] = None

    aliases: Optional[List[str]] = None

    class Config:
        extra = "forbid"


# ============================================================
# OUT
# ============================================================

class SolutionOut(BaseModel):

    id_solution: str

    name: str

    id_company: str

    description: Optional[str] = None

    content: Optional[str] = None

    media_logo_rectangle_id: Optional[str] = None

    aliases: List[str] = Field(default_factory=list)

    created_at: Optional[datetime] = None

    updated_at: Optional[datetime] = None

    has_numbers: Optional[bool] = False

    class Config:
        extra = "forbid"
