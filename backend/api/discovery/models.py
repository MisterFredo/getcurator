from pydantic import BaseModel
from typing import List, Optional, Dict
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
    failed_sources: Optional[int] = None

    class Config:
        extra = "forbid"


# ============================================================
# SCAN ALL REQUEST
# ============================================================

class ScanAllRequest(BaseModel):
    universe_id: Optional[str] = None

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


# ============================================================
# MANUAL DISCOVERY ITEM
# ============================================================

class ManualDiscoveryOut(BaseModel):
    id_discovery: str
    source_id: str
    source_name: Optional[str] = None
    url: str
    title: Optional[str] = None
    date_found: Optional[datetime] = None

    class Config:
        extra = "forbid"


# ============================================================
# MANUAL DISCOVERY LIST
# ============================================================

class ManualDiscoveryListOut(BaseModel):
    status: str
    items: List[ManualDiscoveryOut]

    class Config:
        extra = "forbid"


# ============================================================
# LINKEDIN STUDIO TEST
# ============================================================

class LinkedInStudioTestRequest(BaseModel):
    text: str

    class Config:
        extra = "forbid"


# ============================================================
# LINKEDIN STUDIO
# ============================================================

class LinkedInStudioAnalyzeRequest(BaseModel):
    source_id: str
    text: str

    class Config:
        extra = "forbid"


# ============================================================
# LINKEDIN STUDIO — STORE
# ============================================================

class LinkedInStudioPostIn(BaseModel):
    title: str
    raw_text: str
    date_source: Optional[str] = None

    class Config:
        extra = "forbid"


class LinkedInStudioStoreRequest(BaseModel):
    posts: List[LinkedInStudioPostIn]

    class Config:
        extra = "forbid"


# ============================================================
# NEWSLETTER STUDIO
# ============================================================

class NewsletterStudioItem(BaseModel):
    title: str
    raw_text: str
    date_source: Optional[str] = None
    source_url: Optional[str] = None
    original_source: Optional[str] = None


class NewsletterStudioStoreRequest(BaseModel):
    items: List[NewsletterStudioItem]


# ============================================================
# PDF STUDIO — INSPECT / MAP RESPONSE
# ============================================================

class PDFStudioPageOut(BaseModel):
    page: int
    char_count: int
    image_count: int
    needs_visual_review: bool
    preview: str


class PDFStudioInspectResponse(BaseModel):
    status: str
    document_hash: str
    filename: str
    page_count: int
    title: Optional[str] = None
    author: Optional[str] = None
    pages: List[PDFStudioPageOut]
    low_text_pages: List[int]
    visual_review_pages: List[int]


class PDFStudioDocumentOut(BaseModel):
    document_hash: str
    filename: str
    page_count: int
    title: Optional[str] = None
    author: Optional[str] = None


class PDFStudioQualityOut(BaseModel):
    low_text_pages: List[int]
    visual_review_pages: List[int]


class PDFStudioSectionOut(BaseModel):
    page: int
    heading_candidate: str


class PDFStudioTopicPageOut(BaseModel):
    page: int
    mentions: int


class PDFStudioTopicOut(BaseModel):
    page_count: int
    pages: List[PDFStudioTopicPageOut]


class PDFStudioMapResponse(BaseModel):
    status: str
    document: PDFStudioDocumentOut
    quality: PDFStudioQualityOut
    sections: List[PDFStudioSectionOut]
    topics: Dict[str, PDFStudioTopicOut]
    note: str
