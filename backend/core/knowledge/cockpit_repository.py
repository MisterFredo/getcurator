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


# ============================================================
# COMPANIES
# ============================================================

def _get_companies(
) -> list[KnowledgeEntitySummary]:
    """
    Return every Company displayed in the
    Knowledge Explorer.
    """

    query = """
    ...
    """

    rows = query_bq(
        query,
    ) or []

    return [

        KnowledgeEntitySummary(

            entity_type="company",

            entity_id=row["ID_COMPANY"],

            name=row["NAME"],

            contents_count=row["CONTENTS_COUNT"],

            users_count=row["USERS_COUNT"],

            experts_count=row["EXPERTS_COUNT"],

            has_knowledge=row["HAS_KNOWLEDGE"],

            last_build=row["LAST_BUILD"],

        )

        for row in rows

    ]


# ============================================================
# TOPICS
# ============================================================

def _get_topics(
) -> list[KnowledgeEntitySummary]:

    raise NotImplementedError


# ============================================================
# SOLUTIONS
# ============================================================

def _get_solutions(
) -> list[KnowledgeEntitySummary]:

    raise NotImplementedError

# ============================================================
# EXPLORER
# ============================================================

def list_entities(
) -> KnowledgeExplorer:
    """
    Return every entity displayed in the
    Knowledge Explorer.
    """

    entities = []

    entities.extend(
        _get_companies()
    )

    entities.extend(
        _get_topics()
    )

    entities.extend(
        _get_solutions()
    )

    entities.sort(

        key=lambda entity: (

            -entity.contents_count,

            entity.name,

        ),

    )

    return KnowledgeExplorer(

        entities=entities,

    )
