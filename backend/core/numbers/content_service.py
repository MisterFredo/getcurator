from typing import (
    Any,
    Dict,
    List,
)

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
)


# ============================================================
# TABLES / VIEWS
# ============================================================

VIEW_NUMBER = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "V_NUMBER_OBSERVATION_EFFECTIVE"
)

TABLE_NUMBER_ENTITY = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_NUMBER_OBSERVATION_ENTITY"
)


# ============================================================
# HELPERS
# ============================================================

def _value(
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

    return (
        default
        if value is None
        else value
    )


def _serialize_entities(
    entities,
) -> List[Dict[str, Any]]:

    if not entities:
        return []

    return [
        {
            "entity_type": _value(
                entity,
                "ENTITY_TYPE",
            ),

            "entity_id": _value(
                entity,
                "ENTITY_ID",
            ),

            "entity_label": _value(
                entity,
                "ENTITY_LABEL",
            ),
        }

        for entity in entities
    ]


# ============================================================
# GET ACCEPTED NUMBERS FOR CONTENT
# ============================================================

def get_validated_numbers_for_content(
    id_content: str,
) -> List[Dict[str, Any]]:
    """
    Return only effectively ACCEPTED Numbers
    attached to one content.

    This is the canonical Numbers reader for
    article drawers and future downstream uses.
    """

    normalized_content_id = (
        id_content
        or ""
    ).strip()

    if not normalized_content_id:
        return []

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

                ) AS ENTITIES

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

            entity_aggregation.ENTITIES

        FROM `{VIEW_NUMBER}` number

        LEFT JOIN entity_aggregation
          ON entity_aggregation.ID_NUMBER
             = number.ID_NUMBER

        WHERE number.ID_CONTENT
              = @id_content

          AND number.EFFECTIVE_STATUS
              = 'ACCEPTED'

        ORDER BY

            number.PUBLISHED_AT ASC,

            number.ID_NUMBER ASC
        """,
        {
            "id_content": (
                normalized_content_id
            ),
        },
    ) or []

    return [
        {
            "id_number": _value(
                row,
                "ID_NUMBER",
            ),

            "id_content": _value(
                row,
                "ID_CONTENT",
            ),

            "label": _value(
                row,
                "LABEL",
            ),

            "metric_type": _value(
                row,
                "METRIC_TYPE",
            ),

            "value": _value(
                row,
                "VALUE",
            ),

            "value_min": _value(
                row,
                "VALUE_MIN",
            ),

            "value_max": _value(
                row,
                "VALUE_MAX",
            ),

            "unit": _value(
                row,
                "UNIT",
            ),

            "scale": _value(
                row,
                "SCALE",
            ),

            "zone": _value(
                row,
                "ZONE",
            ),

            "period_label": _value(
                row,
                "PERIOD_LABEL",
            ),

            "value_status": _value(
                row,
                "VALUE_STATUS",
            ),

            "confidence": _value(
                row,
                "CONFIDENCE",
                0,
            ),

            "entities": _serialize_entities(
                _value(
                    row,
                    "ENTITIES",
                    [],
                )
            ),
        }

        for row in rows
    ]
