import re

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

VALID_VALUE_STATUSES = {
    "ACTUAL",
    "FORECAST",
    "TARGET",
    "UNKNOWN",
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
    Convert a SQL fragment beginning with AND or WHERE
    into a standalone condition.
    """

    normalized = (
        condition
        or ""
    ).strip()

    upper = normalized.upper()

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


def _entity_aggregation_sql() -> str:

    return f"""
    entity_aggregation AS (

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

            ARRAY_AGG(
                DISTINCT IF(
                    ENTITY_TYPE = 'company',
                    ENTITY_ID,
                    NULL
                )
                IGNORE NULLS
            ) AS COMPANY_IDS,

            ARRAY_AGG(
                DISTINCT IF(
                    ENTITY_TYPE = 'solution',
                    ENTITY_ID,
                    NULL
                )
                IGNORE NULLS
            ) AS SOLUTION_IDS,

            ARRAY_AGG(
                DISTINCT IF(
                    ENTITY_TYPE = 'topic',
                    ENTITY_ID,
                    NULL
                )
                IGNORE NULLS
            ) AS TOPIC_IDS,

            STRING_AGG(
                DISTINCT ENTITY_LABEL,
                ' '
            ) AS ENTITY_SEARCH

        FROM `{TABLE_NUMBER_ENTITY}`

        GROUP BY
            ID_NUMBER
    )
    """


def _build_scope_conditions(
    user_id: Optional[str] = None,
    universe_id: Optional[str] = None,
    query: Optional[str] = None,
) -> tuple[
    List[str],
    Dict[str, Any],
]:
    """
    Build common visibility conditions used by both
    the public results and their facets.
    """

    conditions = [
        """
        number.EFFECTIVE_STATUS = 'ACCEPTED'
        """,
    ]

    params: Dict[str, Any] = {}

    # ========================================================
    # USER
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

        params["user_id"] = user_id

    # ========================================================
    # UNIVERSE
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
    # QUERY
    # ========================================================

    normalized_query = (
        query
        or ""
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

    return (
        conditions,
        params,
    )


# ============================================================
# SEARCH VALIDATED NUMBERS
# ============================================================

def search_validated_numbers(
    query: Optional[str] = None,
    user_id: Optional[str] = None,
    universe_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    company_id: Optional[str] = None,
    solution_id: Optional[str] = None,
    topic_id: Optional[str] = None,
    metric_type: Optional[str] = None,
    zone: Optional[str] = None,
    period: Optional[str] = None,
    year: Optional[str] = None,
    value_status: Optional[str] = None,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    Search effectively ACCEPTED Numbers.
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

    conditions, params = (
        _build_scope_conditions(
            user_id=user_id,
            universe_id=universe_id,
            query=query,
        )
    )

    params.update({
        "limit": safe_limit,
        "offset": safe_offset,
    })

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
            entity_id.strip()
        )

    # ========================================================
    # COMPANY
    # ========================================================
    
    if company_id:
    
        conditions.append(
            """
            @company_id IN UNNEST(
                IFNULL(
                    entity_aggregation.COMPANY_IDS,
                    ARRAY<STRING>[]
                )
            )
            """
        )
    
        params["company_id"] = (
            company_id.strip()
        )
    
    
    # ========================================================
    # SOLUTION
    # ========================================================
    
    if solution_id:
    
        conditions.append(
            """
            @solution_id IN UNNEST(
                IFNULL(
                    entity_aggregation.SOLUTION_IDS,
                    ARRAY<STRING>[]
                )
            )
            """
        )
    
        params["solution_id"] = (
            solution_id.strip()
        )
    
    
    # ========================================================
    # TOPIC
    # ========================================================
    
    if topic_id:
    
        conditions.append(
            """
            @topic_id IN UNNEST(
                IFNULL(
                    entity_aggregation.TOPIC_IDS,
                    ARRAY<STRING>[]
                )
            )
            """
        )
    
        params["topic_id"] = (
            topic_id.strip()
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
    # EXACT PERIOD
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

    # ========================================================
    # YEAR
    # ========================================================

    if year:

        normalized_year = (
            str(year)
            .strip()
        )

        if not re.fullmatch(
            r"(?:19|20)\d{2}",
            normalized_year,
        ):

            raise ValueError(
                f"Invalid year: {year}"
            )

        conditions.append(
            """
            @year IN UNNEST(
                REGEXP_EXTRACT_ALL(
                    IFNULL(
                        number.PERIOD_LABEL,
                        ''
                    ),
                    r'(?:19|20)\\d{2}'
                )
            )
            """
        )

        params["year"] = (
            normalized_year
        )

    # ========================================================
    # VALUE STATUS
    # ========================================================

    if value_status:

        normalized_value_status = (
            value_status
            .strip()
            .upper()
        )

        if (
            normalized_value_status
            not in VALID_VALUE_STATUSES
        ):

            raise ValueError(
                "Invalid value status: "
                f"{value_status}"
            )

        conditions.append(
            """
            number.VALUE_STATUS
                = @value_status
            """
        )

        params["value_status"] = (
            normalized_value_status
        )

    where_sql = " AND ".join(
        conditions
    )

    # ========================================================
    # QUERY
    # ========================================================

    rows = query_bq(
        f"""
        WITH

        {_entity_aggregation_sql()}

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
        int(
            _row_value(
                rows[0],
                "TOTAL_COUNT",
                0,
            )
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

# ============================================================
# GET PUBLIC NUMBER FILTERS
# ============================================================

def get_validated_number_filters(
    user_id: Optional[str] = None,
    universe_id: Optional[str] = None,
    query: Optional[str] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Return useful business facets for visible,
    effectively ACCEPTED Numbers.
    """

    conditions, params = (
        _build_scope_conditions(
            user_id=user_id,
            universe_id=universe_id,
            query=query,
        )
    )

    where_sql = " AND ".join(
        conditions
    )

    rows = query_bq(
        f"""
        WITH

        {_entity_aggregation_sql()},

        base AS (

            SELECT

                number.ID_NUMBER,

                number.METRIC_TYPE,

                number.ZONE

            FROM `{VIEW_NUMBER}` number

            JOIN `{TABLE_CONTENT}` content
              ON content.id_content
                 = number.ID_CONTENT

            LEFT JOIN entity_aggregation
              ON entity_aggregation.ID_NUMBER
                 = number.ID_NUMBER

            WHERE {where_sql}
        ),

        entity_facets AS (

            SELECT

                entity.ENTITY_TYPE,

                entity.ENTITY_ID,

                ANY_VALUE(
                    entity.ENTITY_LABEL
                ) AS ENTITY_LABEL,

                COUNT(
                    DISTINCT base.ID_NUMBER
                ) AS FACET_COUNT

            FROM base

            JOIN `{TABLE_NUMBER_ENTITY}` entity
              ON entity.ID_NUMBER
                 = base.ID_NUMBER

            WHERE entity.ENTITY_TYPE IN (
                'company',
                'solution',
                'topic'
            )

            GROUP BY

                entity.ENTITY_TYPE,

                entity.ENTITY_ID
        )

        SELECT

            'metric_type'
                AS FACET_TYPE,

            METRIC_TYPE
                AS FACET_VALUE,

            METRIC_TYPE
                AS FACET_LABEL,

            COUNT(*)
                AS FACET_COUNT

        FROM base

        WHERE METRIC_TYPE IS NOT NULL
          AND TRIM(METRIC_TYPE) != ''

        GROUP BY
            METRIC_TYPE

        UNION ALL

        SELECT

            'zone'
                AS FACET_TYPE,

            ZONE
                AS FACET_VALUE,

            ZONE
                AS FACET_LABEL,

            COUNT(*)
                AS FACET_COUNT

        FROM base

        WHERE ZONE IS NOT NULL
          AND TRIM(ZONE) != ''

        GROUP BY
            ZONE

        UNION ALL

        SELECT

            ENTITY_TYPE
                AS FACET_TYPE,

            ENTITY_ID
                AS FACET_VALUE,

            ENTITY_LABEL
                AS FACET_LABEL,

            FACET_COUNT

        FROM entity_facets

        ORDER BY

            FACET_TYPE ASC,

            FACET_COUNT DESC,

            FACET_LABEL ASC
        """,
        params,
    ) or []

    result: Dict[
        str,
        List[Dict[str, Any]],
    ] = {
        "metric_types": [],
        "zones": [],
        "companies": [],
        "solutions": [],
        "topics": [],
    }

    target_by_type = {
        "metric_type":
            "metric_types",

        "zone":
            "zones",

        "company":
            "companies",

        "solution":
            "solutions",

        "topic":
            "topics",
    }

    for row in rows:

        facet_type = _row_value(
            row,
            "FACET_TYPE",
        )

        target = target_by_type.get(
            facet_type
        )

        if not target:
            continue

        value = _row_value(
            row,
            "FACET_VALUE",
        )

        label = _row_value(
            row,
            "FACET_LABEL",
        )

        if value is None:
            continue

        result[target].append({
            "value": str(value),

            "label": (
                str(
                    label
                    or value
                )
                .replace(
                    "_",
                    " ",
                )
                .title()
            ),

            "count": int(
                _row_value(
                    row,
                    "FACET_COUNT",
                    0,
                )
            ),
        })

    return result
