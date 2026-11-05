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

    is_partner: bool = False

    universes: List[str] = Field(default_factory=list)

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

    is_partner: Optional[bool] = None

    wiki_content: Optional[str] = None

    universes: Optional[List[str]] = None

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

    is_partner: bool = False
    is_active: bool = True

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    universes: List[str] = Field(default_factory=list)

    class Config:
        extra = "forbid"

# AJOUTER à la fin de api/company/models.py. Ne pas remplacer le fichier.
from typing import Any, Dict, Literal
from urllib.parse import urlsplit, urlunsplit
from pydantic import validator, root_validator

CompanyWatchSourceType = Literal["HTML", "LINKEDIN", "NEWSLETTER", "PDF"]
CompanyWatchSourceRole = Literal["CORPORATE", "EMPLOYEE"]
# V1: aucun collecteur automatique n'est encore branché.
CompanyWatchCollectionMethod = Literal["MANUAL", "STUDIO"]


class CompanyWatchBase(BaseModel):
    @validator("label", "author_name", check_fields=False, pre=True)
    def clean_text(cls, value):
        if isinstance(value, str):
            value = value.strip()
        return value

    @validator("source_url", check_fields=False, pre=True)
    def clean_url(cls, value):
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("URL attendue")
        parts = urlsplit(value.strip())
        if parts.scheme.lower() not in ("http", "https") or not parts.hostname:
            raise ValueError("URL HTTP(S) absolue requise")
        if parts.username or parts.password:
            raise ValueError("Les identifiants dans les URL sont interdits")
        try:
            parts.port
        except ValueError:
            raise ValueError("Port invalide")
        return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path or "/", parts.query, ""))

    class Config:
        extra = "forbid"
        allow_inf_nan = False


class CompanyWatchCreate(CompanyWatchBase):
    label: str = Field(min_length=1, max_length=250)
    source_type: CompanyWatchSourceType
    source_url: str = Field(max_length=4096)
    source_role: CompanyWatchSourceRole = "CORPORATE"
    author_name: Optional[str] = Field(default=None, max_length=250)
    collection_method: CompanyWatchCollectionMethod = "MANUAL"
    collection_config: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class CompanyWatchUpdate(CompanyWatchBase):
    label: Optional[str] = Field(default=None, min_length=1, max_length=250)
    source_type: Optional[CompanyWatchSourceType] = None
    source_url: Optional[str] = Field(default=None, max_length=4096)
    source_role: Optional[CompanyWatchSourceRole] = None
    author_name: Optional[str] = Field(default=None, max_length=250)
    collection_method: Optional[CompanyWatchCollectionMethod] = None
    collection_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

    @root_validator(pre=True)
    def reject_null_required_fields(cls, values):
        for key, value in values.items():
            if value is None and key != "author_name":
                raise ValueError(f"{key} ne peut pas être null")
        return values


class CompanyWatchOut(CompanyWatchCreate):
    id_company_watch: str
    id_company: str
    company_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

