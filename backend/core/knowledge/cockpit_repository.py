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
# COMPANIES
# ============================================================

def _get_companies(
) -> list[KnowledgeEntitySummary]:
    """
    Return every Company displayed in the
    Knowledge Explorer.
    """

    query = f"""
    WITH CONTENTS AS (

        SELECT

            company.id_company AS ENTITY_ID,

            COUNT(*) AS CONTENTS_COUNT

        FROM `{TABLE_CONTENT}` c

        CROSS JOIN UNNEST(
            c.COMPANIES
        ) company

        WHERE

            c.STATUS = "PUBLISHED"

        AND

            c.IS_ACTIVE = TRUE

        GROUP BY

            company.id_company

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

            TYPE = "company"

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

            TYPE = "company"

        AND

            u.PROFILE_TYPE = "EXPERT"

        GROUP BY

            VALUE_ID

    ),

    KNOWLEDGE AS (

        SELECT

            ENTITY_ID,

            MAX(UPDATED_AT) AS LAST_BUILD

        FROM `{TABLE_KNOWLEDGE}`

        WHERE

            ENTITY_TYPE = "company"

        GROUP BY

            ENTITY_ID

    )

    SELECT

        c.ID_COMPANY,

        c.NAME,

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

        knowledge.LAST_BUILD,

        knowledge.LAST_BUILD IS NOT NULL
            AS HAS_KNOWLEDGE

    FROM `{TABLE_COMPANY}` c

    LEFT JOIN CONTENTS contents

        ON contents.ENTITY_ID = c.ID_COMPANY

    LEFT JOIN USERS users

        ON users.ENTITY_ID = c.ID_COMPANY

    LEFT JOIN EXPERTS experts

        ON experts.ENTITY_ID = c.ID_COMPANY

    LEFT JOIN KNOWLEDGE knowledge

        ON knowledge.ENTITY_ID = c.ID_COMPANY

    ORDER BY

        CONTENTS_COUNT DESC,

        NAME
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
# SOLUTIONS
# ============================================================

def _get_solutions(
) -> list[KnowledgeEntitySummary]:
    """
    Return every Solution displayed in the
    Knowledge Explorer.
    """

    query = f"""
    WITH CONTENTS AS (

        SELECT

            solution.id_solution AS ENTITY_ID,

            COUNT(*) AS CONTENTS_COUNT

        FROM `{TABLE_CONTENT}` c

        CROSS JOIN UNNEST(
            c.SOLUTIONS
        ) solution

        WHERE

            c.STATUS = "PUBLISHED"

        AND

            c.IS_ACTIVE = TRUE

        GROUP BY

            solution.id_solution

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

            TYPE = "solution"

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

            TYPE = "solution"

        AND

            u.PROFILE_TYPE = "EXPERT"

        GROUP BY

            VALUE_ID

    ),

    KNOWLEDGE AS (

        SELECT

            ENTITY_ID,

            MAX(UPDATED_AT) AS LAST_BUILD

        FROM `{TABLE_KNOWLEDGE}`

        WHERE

            ENTITY_TYPE = "solution"

        GROUP BY

            ENTITY_ID

    )

    SELECT

        s.ID_SOLUTION,

        s.NAME,

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

        knowledge.LAST_BUILD,

        knowledge.LAST_BUILD IS NOT NULL
            AS HAS_KNOWLEDGE

    FROM `{TABLE_SOLUTION}` s

    LEFT JOIN CONTENTS contents

        ON contents.ENTITY_ID = s.ID_SOLUTION

    LEFT JOIN USERS users

        ON users.ENTITY_ID = s.ID_SOLUTION

    LEFT JOIN EXPERTS experts

        ON experts.ENTITY_ID = s.ID_SOLUTION

    LEFT JOIN KNOWLEDGE knowledge

        ON knowledge.ENTITY_ID = s.ID_SOLUTION

    ORDER BY

        CONTENTS_COUNT DESC,

        NAME
    """

    rows = query_bq(
        query,
    ) or []

    return [

        KnowledgeEntitySummary(

            entity_type="solution",

            entity_id=row["ID_SOLUTION"],

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
    """
    Return every Topic displayed in the
    Knowledge Explorer.
    """

    query = f"""
    WITH CONTENTS AS (

        SELECT

            topic.id_topic AS ENTITY_ID,

            COUNT(*) AS CONTENTS_COUNT

        FROM `{TABLE_CONTENT}` c

        CROSS JOIN UNNEST(
            c.TOPICS
        ) topic

        WHERE

            c.STATUS = "PUBLISHED"

        AND

            c.IS_ACTIVE = TRUE

        GROUP BY

            topic.id_topic

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

            TYPE = "topic"

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

            TYPE = "topic"

        AND

            u.PROFILE_TYPE = "EXPERT"

        GROUP BY

            VALUE_ID

    ),

    KNOWLEDGE AS (

        SELECT

            ENTITY_ID,

            MAX(UPDATED_AT) AS LAST_BUILD

        FROM `{TABLE_KNOWLEDGE}`

        WHERE

            ENTITY_TYPE = "topic"

        GROUP BY

            ENTITY_ID

    )

    SELECT

        t.ID_TOPIC,

        t.LABEL,

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

        knowledge.LAST_BUILD,

        knowledge.LAST_BUILD IS NOT NULL
            AS HAS_KNOWLEDGE

    FROM `{TABLE_TOPIC}` t

    LEFT JOIN CONTENTS contents

        ON contents.ENTITY_ID = t.ID_TOPIC

    LEFT JOIN USERS users

        ON users.ENTITY_ID = t.ID_TOPIC

    LEFT JOIN EXPERTS experts

        ON experts.ENTITY_ID = t.ID_TOPIC

    LEFT JOIN KNOWLEDGE knowledge

        ON knowledge.ENTITY_ID = t.ID_TOPIC

    ORDER BY

        CONTENTS_COUNT DESC,

        LABEL
    """

    rows = query_bq(
        query,
    ) or []

    return [

        KnowledgeEntitySummary(

            entity_type="topic",

            entity_id=row["ID_TOPIC"],

            name=row["LABEL"],

            contents_count=row["CONTENTS_COUNT"],

            users_count=row["USERS_COUNT"],

            experts_count=row["EXPERTS_COUNT"],

            has_knowledge=row["HAS_KNOWLEDGE"],

            last_build=row["LAST_BUILD"],

        )

        for row in rows

    ]

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
