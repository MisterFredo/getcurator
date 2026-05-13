from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# =========================================================
# CREATE
# =========================================================

class CompanyCreate(BaseModel):

    name: str
    type: Optional[str] = None

    description: Optional[str] = None

    linkedin_url: Optional[str] = None
    website_url: Optional[str] = None
    insight_frequency: Optional[str] = "QUARTERLY"

    is_partner: bool = False

    # 🔥 IMPORTANT → PAS DE LIST MUTABLE PAR DÉFAUT
    universes: List[str] = Field(default_factory=list)

    # 🔥 NEW → alias proposés lors de la création
    aliases: List[str] = Field(default_factory=list)

    class Config:
        extra = "forbid"


# =========================================================
# UPDATE
# =========================================================

class CompanyUpdate(BaseModel):

    name: Optional[str] = None
    type: Optional[str] = None

    description: Optional[str] = None

    linkedin_url: Optional[str] = None
    website_url: Optional[str] = None
    insight_frequency: Optional[str] = None

    is_partner: Optional[bool] = None

    wiki_content: Optional[str] = None

    # 🔥 None = pas de modif / [] = reset
    universes: Optional[List[str]] = None

    # 🔥 NEW → mise à jour possible des alias
    aliases: Optional[List[str]] = None

    class Config:
        extra = "forbid"


# =========================================================
# OUT
# =========================================================

class CompanyOut(BaseModel):

    id_company: str
    name: str

    type: Optional[str] = None

    description: Optional[str] = None

    wiki_content: Optional[str] = None
    wiki_source_id: Optional[str] = None
    wiki_updated_at: Optional[datetime] = None
    wiki_vectorised: Optional[bool] = False

    media_logo_rectangle_id: Optional[str] = None

    linkedin_url: Optional[str] = None
    website_url: Optional[str] = None
    insight_frequency: Optional[str] = None

    is_partner: bool = False
    is_active: bool = True

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # ✅ DATA
    has_numbers: Optional[bool] = False

    # 🔥 TOUJOURS UNE LISTE (important front)
    universes: List[str] = Field(default_factory=list)

    class Config:
        extra = "forbid"
