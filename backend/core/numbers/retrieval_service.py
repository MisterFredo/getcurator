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

from core.user.user_service import (
    build_user_filter,
)


# ============================================================
# TABLES / VIEWS
# ============================================================

VIEW_NUMBER = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "V_NUMBER_OBSERVATION_EFFECTIVE"
)

TABLE_CONTENT = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_CONTENT_ENRICHED"
)

TABLE_NUMBER_ENTITY = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_NUMBER_OBSERVATION_ENTITY"
)


# ============================================================
# CONFIG
# ============================================================

DEFAULT_LIMIT = 50
MAX_LIMIT = 200

VALID_ENTITY_TYPES = {
    "company",
    "topic",
    "solution",
}


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

    return [
        {
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
        }

        for entity in entities
    ]

def _normalize_condition(
    condition: Optional[str],
) -> str:
    """
    Convert a SQL fragment returned as:

        AND (...)
        WHERE (...)

    into a standalone condition that can safely
    be added to the conditions list.
    """

    normalized = (
        condition
        or ""
    ).strip()

    upper = (
        normalized.upper()
    )

    if upper.startswith(
        "AND "
    ):

        normalized = (
            normalized[4:]
            .strip()
        )

    elif upper.startswith(
        "WHERE "
    ):

        normalized = (
            normalized[6:]
            .strip()
        )

    return normalized


# ============================================================
# SEARCH VALIDATED NUMBERS
# ============================================================

def search_validated_numbers(
    query: Optional[str] = None,
    user_id: Optional[str] = None,
    universe_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    metric_type: Optional[str] = None,
    zone: Optional[str] = None,
    period: Optional[str] = None,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    Search effectively ACCEPTED Numbers.

    Raw article Numbers remain available separately
    through the article drawer.
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
        """
        number.EFFECTIVE_STATUS = 'ACCEPTED'
        """,
    ]

    params: Dict[str, Any] = {
        "limit": safe_limit,
        "offset": safe_offset,
    }

    # ========================================================
    # USER FILTER
    # ========================================================
    
    if user_id:
    
        user_condition = (
            _normalize_condition(
                build_user_filter(
                    "content"
                )
            )
        )
    
        if user_condition:
    
            conditions.append(
                user_condition
            )
    
        params["user_id"] = (
            user_id
        )

    # ========================================================
    # UNIVERSE FILTER
    # ========================================================

    if universe_id:

        conditions.append(
            """
            EXISTS (

                SELECT 1

                FROM UNNEST(
                    content.universes
                ) universe

                WHERE universe.id_universe
                      = @universe_id
            )
            """
        )

        params["universe_id"] = (
            universe_id
        )

    # ========================================================
    # SEARCH
    # ========================================================

    normalized_query = (
        query or ""
    ).strip()

    if normalized_query:

        conditions.append(
            """
            (
                LOWER(
                    IFNULL(
                        number.LABEL,
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
                        number.RAW_LINE,
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
                        content.title,
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
                        content.excerpt,
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

        if (
            normalized_entity_type
            not in VALID_ENTITY_TYPES
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

    # ========================================================
    # METRIC TYPE
    # ========================================================

    if metric_type:

        conditions.append(
            """
            number.METRIC_TYPE
                = @metric_type
            """
        )

        params["metric_type"] = (
            metric_type
            .strip()
            .upper()
        )

    # ========================================================
    # ZONE
    # ========================================================

    if zone:

        conditions.append(
            """
            LOWER(
                number.ZONE
            ) = LOWER(
                @zone
            )
            """
        )

        params["zone"] = (
            zone.strip()
        )

    # ========================================================
    # PERIOD
    # ========================================================

    if period:

        conditions.append(
            """
            LOWER(
                number.PERIOD_LABEL
            ) = LOWER(
                @period
            )
            """
        )

        params["period"] = (
            period.strip()
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

            FROM `{TABLE_NUMBER_ENTITY}`

            GROUP BY
                ID_NUMBER
        )

        SELECT

            number.ID_NUMBER,

            number.ID_CONTENT,

            number.LABEL,

            number.METRIC_TYPE,

            number.VALUE,

            number.VALUE_MIN,

            number.VALUE_MAX,

            number.UNIT,

            number.SCALE,

            number.ZONE,

            number.PERIOD_LABEL,

            number.VALUE_STATUS,

            number.CONFIDENCE,

            number.PUBLISHED_AT,

            content.title
                AS CONTENT_TITLE,

            content.excerpt
                AS CONTENT_EXCERPT,

            entity_aggregation.ENTITIES,

            COUNT(*) OVER()
                AS TOTAL_COUNT

        FROM `{VIEW_NUMBER}` number

        JOIN `{TABLE_CONTENT}` content
          ON content.id_content
             = number.ID_CONTENT

        LEFT JOIN entity_aggregation
          ON entity_aggregation.ID_NUMBER
             = number.ID_NUMBER

        WHERE {where_sql}

        ORDER BY

            number.PUBLISHED_AT DESC,

            number.ID_NUMBER ASC

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

            "confidence": _row_value(
                row,
                "CONFIDENCE",
                0,
            ),

            "published_at": (
                _serialize_datetime(
                    _row_value(
                        row,
                        "PUBLISHED_AT",
                    )
                )
            ),

            "content": {
                "id": _row_value(
                    row,
                    "ID_CONTENT",
                ),

                "title": _row_value(
                    row,
                    "CONTENT_TITLE",
                ),

                "excerpt": _row_value(
                    row,
                    "CONTENT_EXCERPT",
                ),
            },

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
