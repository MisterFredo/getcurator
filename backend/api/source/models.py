# backend/api/source/models.py

from datetime import datetime
from typing import (
    List,
    Literal,
    Optional,
)

from pydantic import (
    BaseModel,
    Field,
)


# ============================================================
# ACQUISITION MODE
# ============================================================

AcquisitionMode = Literal[
    "MANUAL",
    "HTML",
    "RSS",
    "SITEMAP",
    "WORDPRESS_API",
    "API",
]


# ============================================================
# CREATE
# ============================================================

class SourceCreate(BaseModel):
    """
    Création d'une source éditoriale.
    Contrat API 100% snake_case.
    """

    name: str = Field(
        ...,
        min_length=1,
    )

    type_source: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[str] = None

    author: Optional[str] = None
    author_profile: Optional[str] = None

    logo: Optional[str] = None

    # ========================================================
    # UNIVERS
    # ========================================================

    universe_id: Optional[str] = None

    # ========================================================
    # ACQUISITION
    # ========================================================

    acquisition_mode: AcquisitionMode = (
        "MANUAL"
    )

    class Config:
        extra = "forbid"


# ============================================================
# UPDATE
# ============================================================

class SourceUpdate(BaseModel):
    """
    Mise à jour partielle d'une source.
    """

    name: Optional[str] = None

    type_source: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[str] = None

    author: Optional[str] = None
    author_profile: Optional[str] = None

    logo: Optional[str] = None

    # ========================================================
    # UNIVERS
    # ========================================================

    universe_id: Optional[str] = None

    # ========================================================
    # ACQUISITION
    # ========================================================

    acquisition_mode: Optional[
        AcquisitionMode
    ] = None

    class Config:
        extra = "forbid"


# ============================================================
# OUT
# ============================================================

class SourceOut(BaseModel):
    """
    Représentation retournée par l'API.
    Snake_case strict.
    """

    source_id: str
    name: str

    type_source: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[str] = None

    author: Optional[str] = None
    author_profile: Optional[str] = None

    logo: Optional[str] = None

    created_at: Optional[datetime] = None

    # ========================================================
    # UNIVERS
    # ========================================================

    universe_id: Optional[str] = None

    # ========================================================
    # ACQUISITION
    # ========================================================

    acquisition_mode: Optional[
        AcquisitionMode
    ] = None

    class Config:
        extra = "forbid"


# ============================================================
# LIST OUT
# ============================================================

class SourceListOut(BaseModel):

    status: str

    sources: List[
        SourceOut
    ]

    class Config:
        extra = "forbid"
