from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Literal
from datetime import datetime, date

class BulkIdsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ids: List[str]
