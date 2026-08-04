# backend/core/knowledge/cockpit_repository.py

from .models import (
    KnowledgeDashboard,
    KnowledgeExplorer,
    KnowledgeEntitySummary,
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
    entity_type: str,
    entity_id: str,
) -> KnowledgeEntitySummary | None:
    """
    Return summary statistics for one entity.
    """

    raise NotImplementedError
