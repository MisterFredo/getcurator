from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============================================================
# CREATE
# ============================================================

class SolutionCreate(BaseModel):
    """
    Création d'une solution.
    Contrat 100% snake_case côté API.
    """

    name: str = Field(..., min_length=1)

    # 🔥 OBLIGATOIRE
    id_company: str

    description: Optional[str] = None
    insight_frequency: Optional[str] = "QUARTERLY"

    content: Optional[str] = None

    status: str = "DRAFT"
    vectorise: bool = False

    # 🔥 NEW → alias produits / marques
    aliases: List[str] = Field(default_factory=list)

    class Config:
        extra = "forbid"


# ============================================================
# UPDATE
# ============================================================

class SolutionUpdate(BaseModel):
    """
    Mise à jour partielle d'une solution.
    """

    name: Optional[str] = None

    # 🔥 autorisé en update
    id_company: Optional[str] = None

    description: Optional[str] = None
    insight_frequency: Optional[str] = None

    content: Optional[str] = None

    status: Optional[str] = None
    vectorise: Optional[bool] = None

    # 🔥 NEW → mise à jour possible des alias
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
    insight_frequency: Optional[str] = None

    content: Optional[str] = None

    status: str
    vectorise: bool

    # 🔥 VISUAL
    media_logo_rectangle_id: Optional[str] = None

    # 🔥 NEW → aliases exposés au front
    aliases: List[str] = Field(default_factory=list)

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    has_numbers: Optional[bool] = False

    class Config:
        extra = "forbid"
