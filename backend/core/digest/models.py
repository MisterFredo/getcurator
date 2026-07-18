# backend/core/digest/models.py

from datetime import datetime

from pydantic import BaseModel, Field

from api.expertise.models import (
    Expertise,
)


# ============================================================
# DIGEST
# ============================================================

class Digest(BaseModel):

    # ========================================================
    # IDENTIFICATION
    # ========================================================

    id: str

    user_id: str

    title: str

    # ========================================================
    # PERIOD
    # ========================================================

    period_start: datetime

    period_end: datetime

    # ========================================================
    # KNOWLEDGE
    # ========================================================

    expertise: Expertise

    capability_results: dict[str, str] = Field(
        default_factory=dict,
    )

    # ========================================================
    # EDITORIAL
    # ========================================================

    intro: str = ""

    outro: str = ""

    # ========================================================
    # LIFECYCLE
    # ========================================================

    status: str = "draft"

    created_at: datetime

    updated_at: datetime

    sent_at: datetime | None = None
