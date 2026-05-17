from pydantic import BaseModel
from typing import Optional, List

# ============================================================
# UNMATCHED ENTITY
# ============================================================

class UnmatchedEntity(BaseModel):

    value: str
    count: int

    type_hint: Optional[str] = None

    suggested_id: Optional[str] = None
    suggested_label: Optional[str] = None

# ============================================================
# MATCH ENTITY
# ============================================================

class EntityMatch(BaseModel):

    alias: str

    target_type: str
    # company | solution | ignore

    target_id: Optional[str] = None

# ============================================================
# BULK MATCH ENTITY
# ============================================================

class BulkEntityMatchItem(BaseModel):

    alias: str

    target_type: str
    # company | solution | ignore

    target_id: Optional[str] = None

class BulkEntityMatchRequest(BaseModel):

    items: List[BulkEntityMatchItem]
