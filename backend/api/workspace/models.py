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
