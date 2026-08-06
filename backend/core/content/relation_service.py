# ============================================================
# IMPORTS
# ============================================================

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
    insert_bq,
)

from core.matching.resolver import (
    normalize,
    resolve_company_alias,
    resolve_solution_alias,
)

# ============================================================
# TABLES
# ============================================================

TABLE_CONTENT = ...
TABLE_CONTENT_COMPANY = ...
TABLE_CONTENT_SOLUTION = ...
TABLE_COMPANY_ALIAS = ...
TABLE_SOLUTION_ALIAS = ...

# ============================================================
# ENTITY RESOLUTION
# ============================================================

def resolve_entities(...):
    ...

# ============================================================
# CONTENT → ENTITIES
# ============================================================

def sync_content_entities(...):
    ...
