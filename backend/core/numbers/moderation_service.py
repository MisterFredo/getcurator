from typing import (
    Any,
    Dict,
    List,
    Optional,
)

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
)


# ============================================================
# TABLES
# ============================================================

VIEW_OBSERVATION = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "V_NUMBER_OBSERVATION_EFFECTIVE"
)

TABLE_OBSERVATION_ENTITY = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_NUMBER_OBSERVATION_ENTITY"
)

TABLE_REVIEW = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_NUMBER_OBSERVATION_REVIEW"
)

TABLE_CONTENT = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_CONTENT_ENRICHED"
)

TABLE_KNOWLEDGE = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_KNOWLEDGE"
)

TABLE_KNOWLEDGE_NUMBER_STATUS = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_KNOWLEDGE_NUMBER_STATUS"
)


# ============================================================
# CONFIG
# ============================================================

VALID_DECISIONS = {
    "ACCEPTED",
    "REVIEW",
    "REJECTED",
}

DEFAULT_LIMIT = 100
MAX_LIMIT = 500
MAX_BULK_IDS = 500


# ============================================================
# HELPERS
# ============================================================

def _serialize_datetime(
    value,
):

    if value is None:
        return None

    if hasattr(
        value,
        "isoformat",
    ):

        return value.isoformat()

    return str(value)


def _row_value(
    row,
    key: str,
    default=None,
):

    try:

        value = row.get(
            key
        )

    except Exception:

        value = None

    if value is None:
        return default

    return value


def _serialize_entities(
    entities,
) -> List[Dict[str, Any]]:

    if not entities:
        return []

    serialized = []

    for entity in entities:

        serialized.append({
            "entity_type": _row_value(
                entity,
                "ENTITY_TYPE",
            ),

            "entity_id": _row_value(
                entity,
                "ENTITY_ID",
            ),

            "entity_label": _row_value(
                entity,
                "ENTITY_LABEL",
            ),
        })

    return serialized


# ============================================================
# LIST OBSERVATIONS
# ============================================================

def list_number_observations(
    status: Optional[str] = None,
    query: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    List transformed Numbers using their effective
    status after manual moderation.
    """

    safe_limit = max(
        1,
        min(
            int(limit),
            MAX_LIMIT,
        ),
    )

    safe_offset = max(
        0,
        int(offset),
    )

    conditions = [
        "TRUE",
    ]

    params: Dict[str, Any] = {
        "limit": safe_limit,
        "offset": safe_offset,
    }

    # ========================================================
    # STATUS
    # ========================================================

    if status:

        normalized_status = (
            status
            .strip()
            .upper()
        )

        if (
            normalized_status
            not in VALID_DECISIONS
        ):

            raise ValueError(
                f"Invalid status: {status}"
            )

        conditions.append(
            """
            observation.EFFECTIVE_STATUS
                = @status
            """
        )

        params["status"] = (
            normalized_status
        )

    # ========================================================
    # SEARCH
    # ========================================================

    if query:

        normalized_query = (
            query.strip()
        )

        if normalized_query:

            conditions.append(
                """
                (
                    LOWER(
                        IFNULL(
                            observation.LABEL,
                            ''
                        )
                    ) LIKE LOWER(
                        CONCAT(
                            '%',
                            @query,
                            '%'
                        )
                    )

                    OR LOWER(
                        IFNULL(
                            observation.RAW_LINE,
                            ''
                        )
                    ) LIKE LOWER(
                        CONCAT(
                            '%',
                            @query,
                            '%'
                        )
                    )

                    OR LOWER(
                        IFNULL(
                            content.TITLE,
                            ''
                        )
                    ) LIKE LOWER(
                        CONCAT(
                            '%',
                            @query,
                            '%'
                        )
                    )

                    OR LOWER(
                        IFNULL(
                            entity_aggregation.ENTITY_SEARCH,
                            ''
                        )
                    ) LIKE LOWER(
                        CONCAT(
                            '%',
                            @query,
                            '%'
                        )
                    )
                )
                """
            )

            params["query"] = (
                normalized_query
            )

    # ========================================================
    # ENTITY TYPE
    # ========================================================

    if entity_type:

        normalized_entity_type = (
            entity_type
            .strip()
            .lower()
        )

        if normalized_entity_type not in (
            "company",
            "topic",
            "solution",
        ):

            raise ValueError(
                "Invalid entity type: "
                f"{entity_type}"
            )

        conditions.append(
            """
            @entity_type IN UNNEST(
                IFNULL(
                    entity_aggregation.ENTITY_TYPES,
                    ARRAY<STRING>[]
                )
            )
            """
        )

        params["entity_type"] = (
            normalized_entity_type
        )

    # ========================================================
    # ENTITY ID
    # ========================================================

    if entity_id:

        conditions.append(
            """
            @entity_id IN UNNEST(
                IFNULL(
                    entity_aggregation.ENTITY_IDS,
                    ARRAY<STRING>[]
                )
            )
            """
        )

        params["entity_id"] = (
            entity_id
        )

    where_sql = " AND ".join(
        conditions
    )

    # ========================================================
    # QUERY
    # ========================================================

    rows = query_bq(
        f"""
        WITH entity_aggregation AS (

            SELECT

                ID_NUMBER,

                ARRAY_AGG(

                    STRUCT(

                        ENTITY_TYPE
                            AS ENTITY_TYPE,

                        ENTITY_ID
                            AS ENTITY_ID,

                        ENTITY_LABEL
                            AS ENTITY_LABEL

                    )

                    ORDER BY
                        ENTITY_TYPE,
                        ENTITY_LABEL

                ) AS ENTITIES,

                ARRAY_AGG(
                    DISTINCT ENTITY_TYPE
                    IGNORE NULLS
                ) AS ENTITY_TYPES,

                ARRAY_AGG(
                    DISTINCT ENTITY_ID
                    IGNORE NULLS
                ) AS ENTITY_IDS,

                STRING_AGG(
                    DISTINCT ENTITY_LABEL,
                    ' '
                ) AS ENTITY_SEARCH

            FROM `{TABLE_OBSERVATION_ENTITY}`

            GROUP BY
                ID_NUMBER
        )

        SELECT

            observation.ID_NUMBER,

            observation.ID_CONTENT,

            content.TITLE AS CONTENT_TITLE,

            observation.RAW_LINE,

            observation.LABEL,

            observation.METRIC_TYPE,

            observation.VALUE,

            observation.VALUE_MIN,

            observation.VALUE_MAX,

            observation.UNIT,

            observation.SCALE,

            observation.ZONE,

            observation.PERIOD_LABEL,

            observation.VALUE_STATUS,

            observation.TRANSFORMER_STATUS,

            observation.EFFECTIVE_STATUS,

            observation.MANUAL_DECISION,

            observation.CONFIDENCE,

            observation.REASON,

            observation.REVIEW_REASON,

            observation.REVIEWED_BY,

            observation.REVIEWED_AT,

            observation.PUBLISHED_AT,

            observation.TRANSFORMER_VERSION,

            entity_aggregation.ENTITIES,

            COUNT(*) OVER() AS TOTAL_COUNT

        FROM `{VIEW_OBSERVATION}` observation

        LEFT JOIN `{TABLE_CONTENT}` content
          ON content.ID_CONTENT
             = observation.ID_CONTENT

        LEFT JOIN entity_aggregation
          ON entity_aggregation.ID_NUMBER
             = observation.ID_NUMBER

        WHERE {where_sql}

        ORDER BY

            observation.PUBLISHED_AT DESC,

            observation.UPDATED_AT DESC,

            observation.ID_NUMBER ASC

        LIMIT @limit

        OFFSET @offset
        """,
        params,
    ) or []

    total = (
        _row_value(
            rows[0],
            "TOTAL_COUNT",
            0,
        )
        if rows
        else 0
    )

    items = []

    for row in rows:

        items.append({
            "id_number": _row_value(
                row,
                "ID_NUMBER",
            ),

            "id_content": _row_value(
                row,
                "ID_CONTENT",
            ),

            "content_title": _row_value(
                row,
                "CONTENT_TITLE",
            ),

            "raw_line": _row_value(
                row,
                "RAW_LINE",
            ),

            "label": _row_value(
                row,
                "LABEL",
            ),

            "metric_type": _row_value(
                row,
                "METRIC_TYPE",
            ),

            "value": _row_value(
                row,
                "VALUE",
            ),

            "value_min": _row_value(
                row,
                "VALUE_MIN",
            ),

            "value_max": _row_value(
                row,
                "VALUE_MAX",
            ),

            "unit": _row_value(
                row,
                "UNIT",
            ),

            "scale": _row_value(
                row,
                "SCALE",
            ),

            "zone": _row_value(
                row,
                "ZONE",
            ),

            "period_label": _row_value(
                row,
                "PERIOD_LABEL",
            ),

            "value_status": _row_value(
                row,
                "VALUE_STATUS",
            ),

            "transformer_status": _row_value(
                row,
                "TRANSFORMER_STATUS",
            ),

            "effective_status": _row_value(
                row,
                "EFFECTIVE_STATUS",
            ),

            "manual_decision": _row_value(
                row,
                "MANUAL_DECISION",
            ),

            "confidence": _row_value(
                row,
                "CONFIDENCE",
                0,
            ),

            "reason": _row_value(
                row,
                "REASON",
            ),

            "review_reason": _row_value(
                row,
                "REVIEW_REASON",
            ),

            "reviewed_by": _row_value(
                row,
                "REVIEWED_BY",
            ),

            "reviewed_at": (
                _serialize_datetime(
                    _row_value(
                        row,
                        "REVIEWED_AT",
                    )
                )
            ),

            "published_at": (
                _serialize_datetime(
                    _row_value(
                        row,
                        "PUBLISHED_AT",
                    )
                )
            ),

            "transformer_version": _row_value(
                row,
                "TRANSFORMER_VERSION",
            ),

            "entities": (
                _serialize_entities(
                    _row_value(
                        row,
                        "ENTITIES",
                        [],
                    )
                )
            ),
        })

    return {
        "items": items,

        "pagination": {
            "total": total,
            "limit": safe_limit,
            "offset": safe_offset,
            "has_more": (
                safe_offset
                + len(items)
                < total
            ),
        },
    }


# ============================================================
# LOAD MODERATION CANDIDATES
# ============================================================

def _load_moderation_candidates(
    ids: List[str],
) -> Dict[str, Dict[str, Any]]:

    rows = query_bq(
        f"""
        WITH entity_counts AS (

            SELECT

                ID_NUMBER,

                COUNT(*) AS ENTITY_COUNT

            FROM `{TABLE_OBSERVATION_ENTITY}`

            GROUP BY
                ID_NUMBER
        )

        SELECT

            observation.ID_NUMBER,

            observation.LABEL,

            observation.METRIC_TYPE,
            observation.EFFECTIVE_STATUS,

            observation.VALUE,

            observation.VALUE_MIN,

            observation.VALUE_MAX,

            observation.UNIT,

            observation.SCALE,

            observation.ZONE,

            observation.PERIOD_LABEL,

            COALESCE(
                entity_counts.ENTITY_COUNT,
                0
            ) > 0 AS HAS_ENTITY

        FROM `{VIEW_OBSERVATION}` observation

        LEFT JOIN entity_counts
          ON entity_counts.ID_NUMBER
             = observation.ID_NUMBER

        WHERE observation.ID_NUMBER
              IN UNNEST(@ids)
        """,
        {
            "ids": ids,
        },
    ) or []

    return {
        row["ID_NUMBER"]: {
            "label": row.get(
                "LABEL"
            ),

            "metric_type": row.get(
                "METRIC_TYPE"
            ),

            "effective_status": row.get(
                "EFFECTIVE_STATUS"
            ),

            "value": row.get(
                "VALUE"
            ),

            "value_min": row.get(
                "VALUE_MIN"
            ),

            "value_max": row.get(
                "VALUE_MAX"
            ),

            "unit": row.get(
                "UNIT"
            ),

            "scale": row.get(
                "SCALE"
            ),

            "zone": row.get(
                "ZONE"
            ),

            "period_label": row.get(
                "PERIOD_LABEL"
            ),

            "has_entity": bool(
                row.get(
                    "HAS_ENTITY"
                )
            ),
        }

        for row in rows
    }


# ============================================================
# ACCEPTANCE VALIDATION
# ============================================================

def _acceptance_error(
    candidate: Dict[str, Any],
) -> Optional[str]:

    required_fields = [
        "label",
        "metric_type",
        "unit",
        "scale",
        "zone",
        "period_label",
    ]

    for field in required_fields:

        if candidate.get(
            field
        ) in (
            None,
            "",
        ):

            return (
                "Missing required field: "
                f"{field}"
            )

    has_single_value = (
        candidate.get(
            "value"
        )
        is not None
    )

    has_complete_range = (
        candidate.get(
            "value_min"
        )
        is not None

        and candidate.get(
            "value_max"
        )
        is not None
    )

    if not (
        has_single_value
        or has_complete_range
    ):

        return (
            "Missing numeric value"
        )

    if not candidate.get(
        "has_entity"
    ):

        return (
            "No official entity assigned"
        )

    return None

# ============================================================
# INVALIDATE NUMBER KNOWLEDGE
# ============================================================

def _invalidate_number_knowledge(
    ids: List[str],
):
    """
    Delete Numbers Knowledge blocks and cursors
    affected by a moderation decision.

    The next Numbers Knowledge run will rebuild
    them from all effectively ACCEPTED observations.
    """

    if not ids:
        return

    # ========================================================
    # DELETE CHIFFRES BLOCKS
    # ========================================================

    query_bq(
        f"""
        DELETE FROM `{TABLE_KNOWLEDGE}`

        WHERE BLOCK_TYPE = 'chiffres'

          AND CONCAT(
              ENTITY_TYPE,
              ':',
              ENTITY_ID
          ) IN (

              SELECT DISTINCT

                  CONCAT(
                      ENTITY_TYPE,
                      ':',
                      ENTITY_ID
                  )

              FROM `{TABLE_OBSERVATION_ENTITY}`

              WHERE ID_NUMBER IN UNNEST(@ids)
          )
        """,
        {
            "ids": ids,
        },
    )

    # ========================================================
    # DELETE NUMBER CURSORS
    # ========================================================

    query_bq(
        f"""
        DELETE FROM `{TABLE_KNOWLEDGE_NUMBER_STATUS}`

        WHERE CONCAT(
            ENTITY_TYPE,
            ':',
            ENTITY_ID
        ) IN (

            SELECT DISTINCT

                CONCAT(
                    ENTITY_TYPE,
                    ':',
                    ENTITY_ID
                )

            FROM `{TABLE_OBSERVATION_ENTITY}`

            WHERE ID_NUMBER IN UNNEST(@ids)
        )
        """,
        {
            "ids": ids,
        },
    )


# ============================================================
# APPLY BULK DECISION
# ============================================================

def apply_number_decisions(
    ids: List[str],
    decision: str,
    reason: Optional[str] = None,
    reviewed_by: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Apply one manual decision to up to 500 Numbers.

    ACCEPTED decisions are applied only to complete
    and entity-linked Numbers.

    Invalid ACCEPTED candidates are skipped without
    blocking the rest of the selection.

    When the effective ACCEPTED perimeter changes,
    the affected Numbers Knowledge blocks and
    cursors are invalidated for a complete rebuild.
    """

    # ========================================================
    # VALIDATE IDS INPUT
    # ========================================================

    if not isinstance(
        ids,
        list,
    ):

        raise ValueError(
            "ids must be an array"
        )

    normalized_ids = list(
        dict.fromkeys([

            str(
                id_number
            ).strip()

            for id_number in ids

            if str(
                id_number
            ).strip()

        ])
    )

    if not normalized_ids:

        raise ValueError(
            "No Number selected"
        )

    if (
        len(normalized_ids)
        > MAX_BULK_IDS
    ):

        raise ValueError(
            "A maximum of 500 Numbers "
            "can be moderated at once"
        )

    # ========================================================
    # VALIDATE DECISION
    # ========================================================

    normalized_decision = (
        str(
            decision
        )
        .strip()
        .upper()
    )

    if (
        normalized_decision
        not in VALID_DECISIONS
    ):

        raise ValueError(
            "Invalid decision: "
            f"{decision}"
        )

    # ========================================================
    # LOAD CANDIDATES
    # ========================================================

    candidates = (
        _load_moderation_candidates(
            ids=normalized_ids,
        )
    )

    updated_ids = []

    skipped = []

    knowledge_change_ids = []

    # ========================================================
    # VALIDATE EACH NUMBER
    # ========================================================

    for id_number in normalized_ids:

        candidate = candidates.get(
            id_number
        )

        # ----------------------------------------------------
        # NUMBER NOT FOUND
        # ----------------------------------------------------

        if candidate is None:

            skipped.append({
                "id_number": (
                    id_number
                ),

                "reason": (
                    "Number not found"
                ),
            })

            continue

        # ----------------------------------------------------
        # ACCEPTANCE REQUIREMENTS
        # ----------------------------------------------------

        if (
            normalized_decision
            == "ACCEPTED"
        ):

            acceptance_error = (
                _acceptance_error(
                    candidate
                )
            )

            if acceptance_error:

                skipped.append({
                    "id_number": (
                        id_number
                    ),

                    "reason": (
                        acceptance_error
                    ),
                })

                continue

        # ----------------------------------------------------
        # CURRENT EFFECTIVE STATUS
        # ----------------------------------------------------

        current_status = (
            candidate.get(
                "effective_status"
            )
        )

        # ----------------------------------------------------
        # KNOWLEDGE INVALIDATION
        # ----------------------------------------------------

        if (
            current_status
            != normalized_decision

            and (

                current_status
                == "ACCEPTED"

                or normalized_decision
                == "ACCEPTED"

            )
        ):

            knowledge_change_ids.append(
                id_number
            )

        # ----------------------------------------------------
        # VALID MODERATION
        # ----------------------------------------------------

        updated_ids.append(
            id_number
        )

    # ========================================================
    # BULK MERGE
    # ========================================================

    if updated_ids:

        query_bq(
            f"""
            MERGE `{TABLE_REVIEW}` target

            USING (

                SELECT

                    id_number
                        AS ID_NUMBER,

                    @decision
                        AS DECISION,

                    @reason
                        AS REASON,

                    @reviewed_by
                        AS REVIEWED_BY

                FROM UNNEST(
                    @ids
                ) id_number

            ) source

            ON target.ID_NUMBER
               = source.ID_NUMBER

            WHEN MATCHED THEN

              UPDATE SET

                DECISION = (
                    source.DECISION
                ),

                REASON = (
                    source.REASON
                ),

                REVIEWED_BY = (
                    source.REVIEWED_BY
                ),

                UPDATED_AT = (
                    CURRENT_TIMESTAMP()
                )

            WHEN NOT MATCHED THEN

              INSERT (

                ID_NUMBER,

                DECISION,

                REASON,

                REVIEWED_BY,

                CREATED_AT,

                UPDATED_AT

              )

              VALUES (

                source.ID_NUMBER,

                source.DECISION,

                source.REASON,

                source.REVIEWED_BY,

                CURRENT_TIMESTAMP(),

                CURRENT_TIMESTAMP()

              )
            """,
            {
                "ids": (
                    updated_ids
                ),

                "decision": (
                    normalized_decision
                ),

                "reason": (
                    reason.strip()
                    if reason
                    else None
                ),

                "reviewed_by": (
                    reviewed_by.strip()
                    if reviewed_by
                    else None
                ),
            },
        )

    # ========================================================
    # INVALIDATE DERIVED KNOWLEDGE
    # ========================================================

    if knowledge_change_ids:

        _invalidate_number_knowledge(
            ids=knowledge_change_ids,
        )

    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "decision": (
            normalized_decision
        ),

        "requested": len(
            normalized_ids
        ),

        "updated": len(
            updated_ids
        ),

        "skipped_count": len(
            skipped
        ),

        "updated_ids": (
            updated_ids
        ),

        "skipped": (
            skipped
        ),

        "knowledge_invalidated_numbers": len(
            knowledge_change_ids
        ),
    }
