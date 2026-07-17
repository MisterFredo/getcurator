from typing import Literal

from pydantic import BaseModel, Field


# ============================================================
# OUTPUT TYPES
# ============================================================

OutputType = Literal[
    "key_points",
    "structure",
    "implications",
]


# ============================================================
# REQUEST
# ============================================================

class WorkspaceGenerateRequest(BaseModel):

    output_type: OutputType

    content_ids: list[str] = Field(
        default_factory=list,
    )

    number_ids: list[str] = Field(
        default_factory=list,
    )

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
