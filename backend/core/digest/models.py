# backend/core/digest/models.py

from datetime import datetime

from pydantic import BaseModel, Field

from api.expertise.models import (
    Expertise,
)

class Digest(BaseModel):

    user_id: str

    period_start: datetime

    period_end: datetime

    expertise: Expertise

    capability_results: dict[str, str]

    intro: str = ""

    outro: str = ""
