# ============================================================
# IA — SUMMARY REQUEST
# ============================================================

class ContentSummaryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: Optional[str] = None
    source_text: str
    id_primary_company: Optional[str] = None
