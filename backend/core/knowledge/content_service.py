# backend/core/knowledge/content_service.py

from .models import (
    KnowledgeContent,
    KnowledgeEntityType,
)


# ============================================================
# LOAD CONTENTS
# ============================================================

def load_contents(
    entity_type: KnowledgeEntityType,
    entity_id: str,
) -> list[KnowledgeContent]:
    """
    Load every enriched content attached
    to one entity.

    Contents are returned from oldest
    to newest.
    """

    match entity_type:

        case "company":
            return _load_company_contents(
                entity_id,
            )

        case "topic":
            return _load_topic_contents(
                entity_id,
            )

        case "solution":
            return _load_solution_contents(
                entity_id,
            )

    return []


# ============================================================
# COMPANY
# ============================================================

def _load_company_contents(
    company_id: str,
) -> list[KnowledgeContent]:

    raise NotImplementedError


# ============================================================
# TOPIC
# ============================================================

def _load_topic_contents(
    topic_id: str,
) -> list[KnowledgeContent]:

    raise NotImplementedError


# ============================================================
# SOLUTION
# ============================================================

def _load_solution_contents(
    solution_id: str,
) -> list[KnowledgeContent]:

    raise NotImplementedError
