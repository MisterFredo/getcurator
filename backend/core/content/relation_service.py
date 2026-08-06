from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
)

from core.matching.resolver import (
    resolve_company_alias,
    resolve_solution_alias,
    resolve_topic_alias,
    resolve_concept_alias,
)

# ============================================================
# TABLES
# ============================================================

TABLE_CONTENT = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"
)

TABLE_CONTENT_COMPANY = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_COMPANY"
)

TABLE_CONTENT_SOLUTION = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_SOLUTION"
)

TABLE_CONTENT_TOPIC = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_TOPIC"
)

TABLE_CONTENT_CONCEPT = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_CONCEPT"
)

# ============================================================
# HELPERS
# ============================================================

def _insert_relation(
    table: str,
    id_field: str,
    id_content: str,
    entity_id: str,
):

    query_bq(
        f"""
        INSERT INTO `{table}` (
            ID_CONTENT,
            {id_field}
        )

        SELECT
            @id_content,
            @entity_id

        WHERE NOT EXISTS (

            SELECT 1

            FROM `{table}`

            WHERE
                ID_CONTENT = @id_content
            AND
                {id_field} = @entity_id

        )
        """,
        {
            "id_content": id_content,
            "entity_id": entity_id,
        },
    )


# ============================================================
# COMPANIES
# ============================================================

def resolve_companies(
    id_content: str,
    acteurs: list[str],
):

    for actor in acteurs:

        id_company = resolve_company_alias(
            actor,
        )

        if id_company:

            _insert_relation(
                TABLE_CONTENT_COMPANY,
                "ID_COMPANY",
                id_content,
                id_company,
            )


# ============================================================
# SOLUTIONS
# ============================================================

def resolve_solutions(
    id_content: str,
    solutions: list[str],
):

    for solution in solutions:

        id_solution = resolve_solution_alias(
            solution,
        )

        if id_solution:

            _insert_relation(
                TABLE_CONTENT_SOLUTION,
                "ID_SOLUTION",
                id_content,
                id_solution,
            )


# ============================================================
# TOPICS
# ============================================================

def resolve_topics(
    id_content: str,
    topics: list[str],
):

    for topic in topics:

        id_topic = resolve_topic_alias(
            topic,
        )

        if id_topic:

            _insert_relation(
                TABLE_CONTENT_TOPIC,
                "ID_TOPIC",
                id_content,
                id_topic,
            )


# ============================================================
# CONCEPTS
# ============================================================

def resolve_concepts(
    id_content: str,
    concepts: list[str],
):

    for concept in concepts:

        id_concept = resolve_concept_alias(
            concept,
        )

        if id_concept:

            _insert_relation(
                TABLE_CONTENT_CONCEPT,
                "ID_CONCEPT",
                id_content,
                id_concept,
            )


# ============================================================
# ALL RELATIONS
# ============================================================

def resolve_all_relations(
    id_content: str,
):

    rows = query_bq(
        f"""
        SELECT
            ACTEURS_CITES,
            SOLUTIONS_LLM,
            TOPICS_LLM,
            CONCEPTS_LLM

        FROM `{TABLE_CONTENT}`

        WHERE ID_CONTENT = @id_content

        LIMIT 1
        """,
        {
            "id_content": id_content,
        },
    )

    if not rows:
        raise ValueError(
            "Content introuvable"
        )

    row = rows[0]

    resolve_companies(
        id_content,
        row.get("ACTEURS_CITES") or [],
    )

    resolve_solutions(
        id_content,
        row.get("SOLUTIONS_LLM") or [],
    )

    resolve_topics(
        id_content,
        row.get("TOPICS_LLM") or [],
    )

    resolve_concepts(
        id_content,
        row.get("CONCEPTS_LLM") or [],
    )
