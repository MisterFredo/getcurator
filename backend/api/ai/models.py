from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Literal
from datetime import datetime, date

# ============================================================
# IA — SUMMARY REQUEST
# ============================================================

class ContentSummaryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: Optional[str] = None
    source_text: str
    id_primary_company: Optional[str] = None
