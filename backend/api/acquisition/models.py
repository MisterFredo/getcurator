from datetime import date
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
)


# ============================================================
# IMPORT TEXT
# ============================================================

class ImportTextRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str

    id_source: str

    id_primary_company: Optional[str] = None


# ============================================================
# IMPORT URLS
# ============================================================

class ImportUrlsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    urls_text: str

    id_source: str

    id_primary_company: Optional[str] = None


# ============================================================
# IMPORT CSV
# ============================================================

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
