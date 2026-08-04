# backend/core/knowledge/cockpit_repository.py

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
)

from .models import (
    KnowledgeDashboard,
    KnowledgeExplorer,
    KnowledgeEntitySummary,
    KnowledgeEntityType,
)


# ============================================================
# TABLES
# ============================================================

TABLE_COMPANY = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY"
)

TABLE_TOPIC = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOPIC"
)

TABLE_SOLUTION = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION"
)

TABLE_CONTENT = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_ENRICHED"
)

TABLE_KNOWLEDGE = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_KNOWLEDGE"
)

TABLE_USER = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER"
)

TABLE_USER_PREFERENCES = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_PREFERENCES"
)


# ============================================================
# DASHBOARD
# ============================================================

def get_dashboard() -> KnowledgeDashboard:
    """
    Return global Knowledge statistics.
    """

    raise NotImplementedError


# ============================================================
# EXPLORER
# ============================================================

def list_entities() -> KnowledgeExplorer:
    """
    Return every entity displayed in the
    Knowledge Explorer.
    """

    raise NotImplementedError


# ============================================================
# ENTITY SUMMARY
# ============================================================

def get_entity_summary(
    entity_type: KnowledgeEntityType,
    entity_id: str,
) -> KnowledgeEntitySummary | None:
    """
    Return summary statistics for one entity.
    """

    raise NotImplementedError
