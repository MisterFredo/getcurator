from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# ============================================================
# DISCOVERY ITEM
# ============================================================

class DiscoveryOut(BaseModel):

    id_discovery: str

    source_id: str
    source_name: Optional[str] = None

    url: str
    title: Optional[str] = None

    status: str

    date_found: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        extra = "forbid"


# ============================================================
# DISCOVERY LIST
# ============================================================

class DiscoveryListOut(BaseModel):

    status: str

    items: List[DiscoveryOut]

    class Config:
        extra = "forbid"


# ============================================================
# SCAN RESPONSE
# ============================================================

class ScanResponse(BaseModel):

    status: str

    scanned_sources: int
    discovered_urls: int

    class Config:
        extra = "forbid"


# ============================================================
# STORE REQUEST
# ============================================================

class StoreRequest(BaseModel):

    discovery_ids: List[str]

    class Config:
        extra = "forbid"


# ============================================================
# STORE RESPONSE
# ============================================================

class StoreResponse(BaseModel):

    status: str

    stored: int
    skipped: int
    errors: int

    class Config:
        extra = "forbid"


# ============================================================
# IGNORE REQUEST
# ============================================================

class IgnoreRequest(BaseModel):

    discovery_ids: List[str]

    class Config:
        extra = "forbid"


# ============================================================
# IGNORE RESPONSE
# ============================================================

class IgnoreResponse(BaseModel):

    status: str

    ignored: int

    class Config:
        extra = "forbid"
