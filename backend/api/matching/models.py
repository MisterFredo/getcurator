from pydantic import BaseModel
from typing import Optional, List

# ===============================================
# LLM SOLUTION
# ===============================================

class LLMSolution(BaseModel):
    value: str
    count: int

# ===============================================
# LLM COMPANY
# ===============================================

class LLMCompany(BaseModel):
    value: str
    count: int

# ===============================================
# MATCH SOLUTION
# ===============================================

class SolutionMatch(BaseModel):

    alias: str
    id_solution: Optional[str] = None
    action: str  # MATCH | IGNORE | CREATE

# ===============================================
# MATCH COMPANY
# ===============================================

class CompanyMatch(BaseModel):

    alias: str
    id_company: Optional[str] = None
    action: str  # MATCH | IGNORE | CREATE

# ===============================================
# BULK MATCH SOLUTION
# ===============================================

class BulkSolutionMatchItem(BaseModel):

    alias: str
    id_solution: Optional[str] = None
    action: str = "MATCH"

class BulkSolutionMatchRequest(BaseModel):

    items: List[BulkSolutionMatchItem]

# ===============================================
# BULK MATCH COMPANY
# ===============================================

class BulkCompanyMatchItem(BaseModel):

    alias: str
    id_company: Optional[str] = None
    action: str = "MATCH"

class BulkCompanyMatchRequest(BaseModel):

    items: List[BulkCompanyMatchItem]
