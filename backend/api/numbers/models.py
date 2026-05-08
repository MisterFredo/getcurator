from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


# ============================================================
# NUMBER (CORE OBJECT)
# ============================================================

class Number(BaseModel):

    id_number: str
    label: Optional[str] = None
    value: float

    unit: Optional[str] = None
    scale: Optional[str] = None

    id_number_type: str

    zone: Optional[str] = None
    period: Optional[str] = None

    source_id: Optional[str] = None

    confidence: Optional[str] = None
    notes: Optional[str] = None

    created_at: datetime
    updated_at: Optional[datetime] = None


# ============================================================
# INPUT (CREATE)
# ============================================================

class NumberInput(BaseModel):

    label: Optional[str] = None
    value: float

    unit: Optional[str] = None
    scale: Optional[str] = None

    id_number_type: str

    zone: Optional[str] = None
    period: Optional[str] = None

    source_id: Optional[str] = None

    confidence: Optional[str] = None
    notes: Optional[str] = None

    company_ids: List[str] = []
    topic_ids: List[str] = []
    solution_ids: List[str] = []

    class Config:
        extra = "forbid"


# ============================================================
# CREATE RESPONSE
# ============================================================

class NumberCreateResponse(BaseModel):

    id_number: str
    quality: Dict  # 🔥 aligné avec ton service


# ============================================================
# PARSED NUMBER (FROM CONTENT)
# ============================================================

class ParsedNumber(BaseModel):

    label: str
    value: float

    unit: Optional[str] = None
    scale: Optional[str] = None

    actor: Optional[str] = None
    zone: Optional[str] = None
    period: Optional[str] = None


# ============================================================
# LIST ITEM
# ============================================================

class NumberListItem(BaseModel):

    id_number: str
    label: Optional[str] = None
    value: float

    unit: Optional[str] = None
    scale: Optional[str] = None

    id_number_type: str

    zone: Optional[str] = None
    period: Optional[str] = None

    confidence: Optional[str] = None

    created_at: datetime
    updated_at: Optional[datetime] = None


# ============================================================
# FEED ITEM (CARDS / UI)
# ============================================================

class NumberFeedItem(BaseModel):

    id_number: str
    label: Optional[str] = None
    value: Optional[float] = None

    unit: Optional[str] = None
    scale: Optional[str] = None

    zone: Optional[str] = None
    period: Optional[str] = None

    type: Optional[str] = None
    category: Optional[str] = None

    entities: Optional[List[Dict]] = []

    universes: Optional[List[str]] = []

    created_at: Optional[datetime] = None
