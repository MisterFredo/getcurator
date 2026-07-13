from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ============================================================
# CREATE
# ============================================================

class TopicCreate(BaseModel):

    label: str = Field(
        ...,
        min_length=1,
    )

    description: Optional[str] = None

    seo_title: Optional[str] = None

    seo_description: Optional[str] = None

    universe_ids: List[str] = Field(
        default_factory=list,
    )

    class Config:
        extra = "forbid"


# ============================================================
# UPDATE
# ============================================================

class TopicUpdate(BaseModel):

    label: Optional[str] = None

    description: Optional[str] = None

    seo_title: Optional[str] = None

    seo_description: Optional[str] = None

    media_square_id: Optional[str] = None

    media_rectangle_id: Optional[str] = None

    universe_ids: Optional[List[str]] = None

    class Config:
        extra = "forbid"


# ============================================================
# OUT
# ============================================================

class TopicOut(BaseModel):

    id_topic: str

    label: str

    description: Optional[str] = None

    seo_title: Optional[str] = None

    seo_description: Optional[str] = None

    media_square_id: Optional[str] = None

    media_rectangle_id: Optional[str] = None

    universes: List[dict] = Field(
        default_factory=list,
    )

    is_active: bool = True

    created_at: Optional[datetime] = None

    updated_at: Optional[datetime] = None

    class Config:
        extra = "forbid"
