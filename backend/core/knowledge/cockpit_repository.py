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

TABLE_KNOWLEDGE_STATUS = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_KNOWLEDGE_STATUS"
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

def get_dashboard(
) -> KnowledgeDashboard:
    """
    Return global Knowledge statistics.
    """

    companies = query_bq(
        f"""
        SELECT COUNT(*) AS TOTAL
        FROM `{TABLE_COMPANY}`
        """
    )[0]["TOTAL"]

    topics = query_bq(
        f"""
        SELECT COUNT(*) AS TOTAL
        FROM `{TABLE_TOPIC}`
        """
    )[0]["TOTAL"]

    solutions = query_bq(
        f"""
        SELECT COUNT(*) AS TOTAL
        FROM `{TABLE_SOLUTION}`
        """
    )[0]["TOTAL"]

    knowledge_built = query_bq(
        f"""
        SELECT

            COUNT(
                DISTINCT CONCAT(
                    ENTITY_TYPE,
                    ":",
                    ENTITY_ID
                )
            ) AS TOTAL

        FROM `{TABLE_KNOWLEDGE}`
        """
    )[0]["TOTAL"]

    users = query_bq(
        f"""
        SELECT COUNT(*) AS TOTAL

        FROM `{TABLE_USER}`

        WHERE

            PROFILE_TYPE = "USER"

        AND

            IS_ACTIVE = TRUE
        """
    )[0]["TOTAL"]

    experts = query_bq(
        f"""
        SELECT COUNT(*) AS TOTAL

        FROM `{TABLE_USER}`

        WHERE

            PROFILE_TYPE = "EXPERT"

        AND

            IS_ACTIVE = TRUE
        """
    )[0]["TOTAL"]

    return KnowledgeDashboard(

        companies=companies,

        topics=topics,

        solutions=solutions,

        entities=(
            companies
            + topics
            + solutions
        ),

        knowledge_built=knowledge_built,

        users=users,

        experts=experts,

    )


# ============================================================
# LIST ENTITIES
# ============================================================

def _list_entities(
    *,
    entity_type: KnowledgeEntityType,
    table: str,
    id_column: str,
    name_column: str,
    array_name: str,
    array_id: str,
) -> list[KnowledgeEntitySummary]:
    """
    Generic loader used by Companies,
    Topics and Solutions.
    """

    query = f"""
    WITH CONTENTS AS (

        SELECT

            entity.{array_id} AS ENTITY_ID,

            COUNT(*) AS CONTENTS_COUNT

        FROM `{TABLE_CONTENT}` c

        CROSS JOIN UNNEST(
            c.{array_name}
        ) entity

        WHERE

            c.STATUS = "PUBLISHED"

        AND

            c.IS_ACTIVE = TRUE

        GROUP BY

            entity.{array_id}

    ),

    USERS AS (

        SELECT

            VALUE_ID AS ENTITY_ID,

            COUNT(
                DISTINCT p.ID_USER
            ) AS USERS_COUNT

        FROM `{TABLE_USER_PREFERENCES}` p

        JOIN `{TABLE_USER}` u

            ON u.ID_USER = p.ID_USER

        WHERE

            TYPE = @entity_type

        AND

            u.PROFILE_TYPE = "USER"

        GROUP BY

            VALUE_ID

    ),

    EXPERTS AS (

        SELECT

            VALUE_ID AS ENTITY_ID,

            COUNT(
                DISTINCT p.ID_USER
            ) AS EXPERTS_COUNT

        FROM `{TABLE_USER_PREFERENCES}` p

        JOIN `{TABLE_USER}` u

            ON u.ID_USER = p.ID_USER

        WHERE

            TYPE = @entity_type

        AND

            u.PROFILE_TYPE = "EXPERT"

        GROUP BY

            VALUE_ID

    ),

    KNOWLEDGE_STATUS AS (

        SELECT

            ENTITY_ID,

            LAST_CONTENT_DATE,

            UPDATED_AT

        FROM `{TABLE_KNOWLEDGE_STATUS}`

        WHERE

            ENTITY_TYPE = @entity_type

    )

    SELECT

        e.{id_column} AS ENTITY_ID,

        e.{name_column} AS NAME,

        COALESCE(
            contents.CONTENTS_COUNT,
            0
        ) AS CONTENTS_COUNT,

        COALESCE(
            users.USERS_COUNT,
            0
        ) AS USERS_COUNT,

        COALESCE(
            experts.EXPERTS_COUNT,
            0
        ) AS EXPERTS_COUNT,

        ks.LAST_CONTENT_DATE,

        ks.UPDATED_AT,

        CASE

            WHEN ks.LAST_CONTENT_DATE IS NULL

            THEN 0

            ELSE (

                SELECT COUNT(*)

                FROM `{TABLE_CONTENT}` c2

                CROSS JOIN UNNEST(
                    c2.{array_name}
                ) entity

                WHERE

                    entity.{array_id} = e.{id_column}

                AND

                    c2.STATUS = "PUBLISHED"

                AND

                    c2.IS_ACTIVE = TRUE

                AND

                    c2.PUBLISHED_AT <= ks.LAST_CONTENT_DATE

            )

        END AS PROCESSED_CONTENTS

    FROM `{table}` e

    LEFT JOIN CONTENTS contents

        ON contents.ENTITY_ID = e.{id_column}

    LEFT JOIN USERS users

        ON users.ENTITY_ID = e.{id_column}

    LEFT JOIN EXPERTS experts

        ON experts.ENTITY_ID = e.{id_column}

    LEFT JOIN KNOWLEDGE_STATUS ks

        ON ks.ENTITY_ID = e.{id_column}

    ORDER BY

        CONTENTS_COUNT DESC,

        NAME
    """

    rows = query_bq(

        query,

        {

            "entity_type": entity_type,

        },

    ) or []

    return [

        KnowledgeEntitySummary(

            entity_type=entity_type,

            entity_id=row["ENTITY_ID"],

            name=row["NAME"],

            contents_count=row["CONTENTS_COUNT"],

            processed_contents=row["PROCESSED_CONTENTS"],

            users_count=row["USERS_COUNT"],

            experts_count=row["EXPERTS_COUNT"],

            last_content_date=row["LAST_CONTENT_DATE"],

            updated_at=row["UPDATED_AT"],

        )

        for row in rows

    ]

# ============================================================
# COMPANIES
# ============================================================

def _get_companies(
) -> list[KnowledgeEntitySummary]:

    return _list_entities(

        entity_type="company",

        table=TABLE_COMPANY,

        id_column="ID_COMPANY",

        name_column="NAME",

        array_name="COMPANIES",

        array_id="id_company",

    )

# ============================================================
# TOPICS
# ============================================================

def _get_topics(
) -> list[KnowledgeEntitySummary]:

    return _list_entities(

        entity_type="topic",

        table=TABLE_TOPIC,

        id_column="ID_TOPIC",

        name_column="LABEL",

        array_name="TOPICS",

        array_id="id_topic",

    )

# ============================================================
# SOLUTIONS
# ============================================================

def _get_solutions(
) -> list[KnowledgeEntitySummary]:

    return _list_entities(

        entity_type="solution",

        table=TABLE_SOLUTION,

        id_column="ID_SOLUTION",

        name_column="NAME",

        array_name="SOLUTIONS",

        array_id="id_solution",

    )
# ============================================================
# EXPLORER
# ============================================================
def list_entities(
) -> KnowledgeExplorer:
    """
    Return every entity displayed in the
    Knowledge Explorer.
    """

    entities = (

        _get_companies()

        + _get_topics()

        + _get_solutions()

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
