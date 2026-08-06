from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Literal
from datetime import datetime, date


# ============================================================
# RAW — STORE
# ============================================================

class ContentRawCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: str
    source_title: str
    source_url: Optional[str] = None
    discovery_id: Optional[str] = None
    raw_text: str

    date_source: Optional[date] = None

    # 🔥 NEW
    id_primary_company: Optional[str] = None


class ContentRawUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # 🔥 NEW
    id_primary_company: Optional[str] = None

    source_title: Optional[str] = None
    source_url: Optional[str] = None
    date_source: Optional[date] = None
    raw_text: Optional[str] = None


class ContentRawOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id_raw: str
    source_id: str
    source_url: Optional[str] = None
    source_title: str

    # 🔥 NEW
    id_primary_company: Optional[str] = None

    date_source: Optional[date] = None

    status: str
    created_at: datetime


class ContentRawDestockRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id_raw: Optional[str] = None
    limit: int = 20



class ImportUrlsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    urls_text: str

    id_source: str

    id_primary_company: Optional[str] = None

class ImportCsvRequest(BaseModel):
    csv_text: str
    id_source: str

