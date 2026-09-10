from typing import (
    Any,
    Dict,
)

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
)

from .number_builder_service import (
    build_number_knowledge,
)


# ============================================================
# TABLES
# ============================================================

TABLE_KNOWLEDGE = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_KNOWLEDGE"
)

TABLE_NUMBER = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_NUMBER_OBSERVATION"
)

TABLE_NUMBER_ENTITY = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_NUMBER_OBSERVATION_ENTITY"
)

TABLE_NUMBER_STATUS = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_KNOWLEDGE_NUMBER_STATUS"
)


# ============================================================
# CONFIG
# ============================================================

DEFAULT_ENTITY_BATCH_SIZE = 5
MAX_ENTITY_BATCH_SIZE = 10


# ============================================================
# LOAD ELIGIBLE ENTITIES
# ============================================================

def load_number_knowledge_entities(
    limit: int = DEFAULT_ENTITY_BATCH_SIZE,
) -> list[Dict[str, Any]]:
    """
    Load entities that:

    - already belong to the general Knowledge perimeter;
    - have at least one ACCEPTED Number;
    - have at least one Number after their Numbers cursor.
    """

    safe_limit = max(
        1,
        min(
            int(limit),
            MAX_ENTITY_BATCH_SIZE,
        ),
    )

    rows = query_bq(
        f"""
        WITH general_knowledge_entities AS (

            SELECT DISTINCT

                ENTITY_TYPE,

                ENTITY_ID

            FROM `{TABLE_KNOWLEDGE}`

            WHERE BLOCK_TYPE IN (
                'signal_analytique',
                'mecanique_expliquee',
                'enjeu_strategique',
                'point_de_friction'
            )
        ),

        eligible_numbers AS (

            SELECT

                relation.ENTITY_TYPE,

                relation.ENTITY_ID,

                relation.ENTITY_LABEL,

                number.ID_NUMBER,

                number.PUBLISHED_AT

            FROM `{TABLE_NUMBER}` number

            JOIN `{TABLE_NUMBER_ENTITY}` relation
              ON relation.ID_NUMBER = number.ID_NUMBER

            JOIN general_knowledge_entities knowledge
              ON knowledge.ENTITY_TYPE = relation.ENTITY_TYPE
             AND knowledge.ENTITY_ID = relation.ENTITY_ID

            LEFT JOIN `{TABLE_NUMBER_STATUS}` status
              ON status.ENTITY_TYPE = relation.ENTITY_TYPE
             AND status.ENTITY_ID = relation.ENTITY_ID

            WHERE number.STATUS = 'ACCEPTED'

              AND number.PUBLISHED_AT IS NOT NULL

              AND (

                  status.ENTITY_ID IS NULL

                  OR number.PUBLISHED_AT
                     > status.LAST_PUBLISHED_AT

                  OR (
                      number.PUBLISHED_AT
                          = status.LAST_PUBLISHED_AT

                      AND number.ID_NUMBER
                          > COALESCE(
                              status.LAST_NUMBER_ID,
                              ''
                          )
                  )
              )
        )

        SELECT

            ENTITY_TYPE,

            ENTITY_ID,

            ANY_VALUE(
                ENTITY_LABEL
            ) AS ENTITY_LABEL,

            COUNT(*) AS PENDING_OBSERVATIONS,

            MIN(
                PUBLISHED_AT
            ) AS FIRST_PENDING_AT,

            MAX(
                PUBLISHED_AT
            ) AS LAST_PENDING_AT

        FROM eligible_numbers

        GROUP BY
            ENTITY_TYPE,
            ENTITY_ID

        ORDER BY
            FIRST_PENDING_AT ASC,
            ENTITY_TYPE ASC,
            ENTITY_ID ASC

        LIMIT @limit
        """,
        {
            "limit": safe_limit,
        },
    ) or []

    return rows

# ============================================================
# NUMBER KNOWLEDGE MONITORING
# ============================================================

def get_number_knowledge_status() -> Dict[str, Any]:
    """
    Return the Numbers Knowledge progress for
    entities already selected in general Knowledge.
    """

    rows = query_bq(
        f"""
        WITH general_knowledge_entities AS (

            SELECT DISTINCT

                ENTITY_TYPE,

                ENTITY_ID

            FROM `{TABLE_KNOWLEDGE}`

            WHERE BLOCK_TYPE IN (
                'signal_analytique',
                'mecanique_expliquee',
                'enjeu_strategique',
                'point_de_friction'
            )
        ),

        accepted_numbers AS (

            SELECT

                relation.ENTITY_TYPE,

                relation.ENTITY_ID,

                relation.ENTITY_LABEL,

                number.ID_NUMBER,

                number.PUBLISHED_AT

            FROM `{TABLE_NUMBER}` number

            JOIN `{TABLE_NUMBER_ENTITY}` relation
              ON relation.ID_NUMBER = number.ID_NUMBER

            JOIN general_knowledge_entities knowledge
              ON knowledge.ENTITY_TYPE
                 = relation.ENTITY_TYPE

             AND knowledge.ENTITY_ID
                 = relation.ENTITY_ID

            WHERE number.STATUS = 'ACCEPTED'

              AND number.PUBLISHED_AT IS NOT NULL
        ),

        entity_state AS (

            SELECT

                accepted.ENTITY_TYPE,

                accepted.ENTITY_ID,

                ANY_VALUE(
                    accepted.ENTITY_LABEL
                ) AS ENTITY_LABEL,

                COUNT(*) AS TOTAL_OBSERVATIONS,

                COUNTIF(

                    status.ENTITY_ID IS NULL

                    OR status.LAST_PUBLISHED_AT
                       IS NULL

                    OR accepted.PUBLISHED_AT
                       > status.LAST_PUBLISHED_AT

                    OR (
                        accepted.PUBLISHED_AT
                            = status.LAST_PUBLISHED_AT

                        AND accepted.ID_NUMBER
                            > COALESCE(
                                status.LAST_NUMBER_ID,
                                ''
                            )
                    )

                ) AS PENDING_OBSERVATIONS,

                ANY_VALUE(
                    status.ENTITY_ID
                ) IS NOT NULL
                    AS HAS_NUMBER_STATUS

            FROM accepted_numbers accepted

            LEFT JOIN `{TABLE_NUMBER_STATUS}` status
              ON status.ENTITY_TYPE
                 = accepted.ENTITY_TYPE

             AND status.ENTITY_ID
                 = accepted.ENTITY_ID

            GROUP BY

                accepted.ENTITY_TYPE,

                accepted.ENTITY_ID
        )

        SELECT

            COUNT(*) AS TOTAL_ENTITIES,

            COUNTIF(
                HAS_NUMBER_STATUS
            ) AS STARTED_ENTITIES,

            COUNTIF(
                HAS_NUMBER_STATUS
                AND PENDING_OBSERVATIONS = 0
            ) AS UP_TO_DATE_ENTITIES,

            COUNTIF(
                PENDING_OBSERVATIONS > 0
            ) AS PENDING_ENTITIES,

            COUNTIF(
                NOT HAS_NUMBER_STATUS
            ) AS NOT_STARTED_ENTITIES,

            COALESCE(
                SUM(TOTAL_OBSERVATIONS),
                0
            ) AS TOTAL_OBSERVATIONS,

            COALESCE(
                SUM(PENDING_OBSERVATIONS),
                0
            ) AS PENDING_OBSERVATIONS,

            COALESCE(
                SUM(
                    TOTAL_OBSERVATIONS
                    - PENDING_OBSERVATIONS
                ),
                0
            ) AS PROCESSED_OBSERVATIONS,

            ROUND(
                SAFE_DIVIDE(

                    SUM(
                        TOTAL_OBSERVATIONS
                        - PENDING_OBSERVATIONS
                    ),

                    SUM(
                        TOTAL_OBSERVATIONS
                    )

                ) * 100,
                2
            ) AS PROGRESS_PERCENT

        FROM entity_state
        """,
        {},
    ) or []

    if not rows:

        return {
            "total_entities": 0,
            "started_entities": 0,
            "up_to_date_entities": 0,
            "pending_entities": 0,
            "not_started_entities": 0,
            "total_observations": 0,
            "processed_observations": 0,
            "pending_observations": 0,
            "progress_percent": 0,
        }

    row = rows[0]

    return {
        "total_entities": (
            row.get("TOTAL_ENTITIES")
            or 0
        ),

        "started_entities": (
            row.get("STARTED_ENTITIES")
            or 0
        ),

        "up_to_date_entities": (
            row.get("UP_TO_DATE_ENTITIES")
            or 0
        ),

        "pending_entities": (
            row.get("PENDING_ENTITIES")
            or 0
        ),

        "not_started_entities": (
            row.get("NOT_STARTED_ENTITIES")
            or 0
        ),

        "total_observations": (
            row.get("TOTAL_OBSERVATIONS")
            or 0
        ),

        "processed_observations": (
            row.get("PROCESSED_OBSERVATIONS")
            or 0
        ),

        "pending_observations": (
            row.get("PENDING_OBSERVATIONS")
            or 0
        ),

        "progress_percent": (
            row.get("PROGRESS_PERCENT")
            or 0
        ),
    }


# ============================================================
# CONTINUE NUMBER KNOWLEDGE
# ============================================================

def continue_number_knowledge(
    limit: int = DEFAULT_ENTITY_BATCH_SIZE,
) -> Dict[str, Any]:
    """
    Process the next group of selected Knowledge
    entities having pending ACCEPTED Numbers.

    Each entity processes at most one batch of
    Number observations per execution.
    """

    entities = load_number_knowledge_entities(
        limit=limit,
    )

    if not entities:

        return {
            "status": "completed",
            "selected_entities": 0,
            "built_entities": 0,
            "no_data_entities": 0,
            "failed_entities": 0,
            "results": [],
            "failures": [],
        }

    results = []
    failures = []

    built_entities = 0
    no_data_entities = 0

    # ========================================================
    # BUILD EACH SELECTED ENTITY
    # ========================================================

    for entity in entities:

        entity_type = entity[
            "ENTITY_TYPE"
        ]

        entity_id = entity[
            "ENTITY_ID"
        ]

        try:

            result = build_number_knowledge(
                entity_type=entity_type,
                entity_id=entity_id,
            )

            result_status = result.get(
                "status"
            )

            if result_status == "built":

                built_entities += 1

            else:

                no_data_entities += 1

            results.append({
                "entity_type": entity_type,

                "entity_id": entity_id,

                "entity_label": entity.get(
                    "ENTITY_LABEL"
                ),

                "pending_observations_before": (
                    entity.get(
                        "PENDING_OBSERVATIONS"
                    )
                ),

                "result": result,
            })

        except Exception as error:

            failures.append({
                "entity_type": entity_type,

                "entity_id": entity_id,

                "entity_label": entity.get(
                    "ENTITY_LABEL"
                ),

                "error": str(error),
            })

    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "status": (
            "partial"
            if failures
            else "processed"
        ),

        "selected_entities": len(
            entities
        ),

        "built_entities": (
            built_entities
        ),

        "no_data_entities": (
            no_data_entities
        ),

        "failed_entities": len(
            failures
        ),

        "results": results,

        "failures": failures,
    }
