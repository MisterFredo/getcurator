from pydantic import (
    BaseModel,
    Field,
)

from typing import (
    Optional,
    List,
)


# =========================================================
# TRANSLATE ONE CONTENT
# =========================================================

class TranslationRequest(BaseModel):

    content_id: str

    target_lang: str = "en"

    fields: List[str] = Field(
        default_factory=lambda: [
            "TITLE",
            "EXCERPT",
        ]
    )

    class Config:
        extra = "forbid"


# =========================================================
# TRANSLATE BATCH
# =========================================================

class TranslationBatchRequest(
    BaseModel
):

    target_lang: str = "en"

    fields: List[str] = Field(
        default_factory=lambda: [
            "TITLE",
            "EXCERPT",
        ]
    )

    limit: int = 10000

    only_missing: bool = True

    # 🔥 OPTIONNEL
    content_ids: Optional[
        List[str]
    ] = None

    # 🔥 FILTERS
    source_id: Optional[str] = None
    class Config:
        extra = "forbid"
