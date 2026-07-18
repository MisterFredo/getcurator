from typing import Literal

from pydantic import BaseModel, Field

from core.expertise.capabilities import (
    CAPABILITY_KEY_POINTS,
    CAPABILITY_STRUCTURE,
    CAPABILITY_IMPLICATIONS,
)

# ============================================================
# TYPES
# ============================================================

Capability = Literal[
    CAPABILITY_KEY_POINTS,
    CAPABILITY_STRUCTURE,
    CAPABILITY_IMPLICATIONS,
]

# ============================================================
# REQUEST
# ============================================================

class WorkspaceGenerateRequest(BaseModel):

    capability: Capability

    content_ids: list[str] = Field(
        default_factory=list,
    )

    number_ids: list[str] = Field(
        default_factory=list,
    )


# ============================================================
# NUMBER
# ============================================================

class WorkspaceNumber(BaseModel):

    id_number: str

    label: str

    value: float | None = None
    unit: str | None = None
    scale: str | None = None

    type: str | None = None
    category: str | None = None

    zone: str | None = None
    period: str | None = None

    entity_label: str | None = None
