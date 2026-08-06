from datetime import date, datetime
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
)


# ============================================================
# RAW
# ============================================================

class ContentRawCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str

    source_title: str

    source_url: Optional[str] = None

    discovery_id: Optional[str] = None

    raw_text: str

    date_source: Optional[date] = None

    id_primary_company: Optional[str] = None


class ContentRawUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_title: Optional[str] = None

    source_url: Optional[str] = None

    raw_text: Optional[str] = None

    date_source: Optional[date] = None

    id_primary_company: Optional[str] = None


class ContentRawOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id_raw: str

    source_id: str

    source_title: str

    source_url: Optional[str] = None

    date_source: Optional[date] = None

    status: str

    created_at: datetime

    id_primary_company: Optional[str] = None


# ============================================================
# IMPORTS
# ============================================================

class ImportTextRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str

    id_source: str

    id_primary_company: Optional[str] = None


class ImportUrlsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    urls_text: str

    id_source: str

    id_primary_company: Optional[str] = None


class ImportCsvRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    csv_text: str

    id_source: str


# ============================================================
# DESTOCK
# ============================================================

class ContentRawDestockRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id_raw: Optional[str] = None

    limit: int = 20
