# backend/core/workspace/number_service.py

from api.workspace.models import (
    WorkspaceNumber,
)

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
)


# ============================================================
# TABLE
# ============================================================

TABLE_NUMBERS = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS"
)


# ============================================================
# LOAD NUMBERS BY IDS
# ============================================================

def load_numbers_by_ids(
    number_ids: list[str],
) -> list[WorkspaceNumber]:

    if not number_ids:
        return []

    rows = query_bq(

        f"""
        SELECT

            ID_NUMBER,

            LABEL,
            VALUE,
            UNIT,
            SCALE,

            TYPE,
            CATEGORY,

            ZONE,
            PERIOD,

            ENTITY_LABEL

        FROM `{TABLE_NUMBERS}`

        WHERE ID_NUMBER IN UNNEST(@number_ids)
        """,

        {
            "number_ids": number_ids,
        },

    ) or []

    return [

        WorkspaceNumber(

            id_number=row.get("ID_NUMBER"),

            label=row.get("LABEL"),

            value=row.get("VALUE"),
            unit=row.get("UNIT"),
            scale=row.get("SCALE"),

            type=row.get("TYPE"),
            category=row.get("CATEGORY"),

            zone=row.get("ZONE"),
            period=row.get("PERIOD"),

            entity_label=row.get("ENTITY_LABEL"),

        )

        for row in rows

    ]
