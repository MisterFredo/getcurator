from typing import List, Literal, Optional

from pydantic import BaseModel


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

class WorkspaceGenerateRequest(
    BaseModel
):

    output_type: OutputType

    content_ids: Optional[List[str]] = []

    number_ids: Optional[List[str]] = []
