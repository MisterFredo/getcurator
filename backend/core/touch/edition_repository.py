import json

from datetime import datetime
from uuid import NAMESPACE_URL, uuid5

from config import BQ_DATASET, BQ_PROJECT
from utils.bigquery_utils import query_bq


TABLE_TOUCH_EDITION = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOUCH_EDITION"
)


# ============================================================
# IDENTITY AND READ
# ============================================================

def build_touch_edition_id(
    expert_id: str,
    period_start: datetime,
) -> str:
    """One stable identity per expert and complete UTC calendar month."""
    return str(uuid5(
        NAMESPACE_URL,
        f"getcurator:touch:{expert_id}:{period_start:%Y-%m}",
    ))


def get_touch_edition(
    edition_id: str,
) -> dict | None:

    rows = query_bq(
        f"""
        SELECT *
        FROM `{TABLE_TOUCH_EDITION}`
        WHERE EDITION_ID = @edition_id
        LIMIT 1
        """,
        {"edition_id": edition_id},
    ) or []

    if not rows:
        return None

    row = rows[0]
    search = row.get("SEARCH_JSON")
    if isinstance(search, str):
        search = json.loads(search)

    def timestamp(name):
        value = row.get(name)
        return value.isoformat() if value is not None else None

    return {
        "edition_id": row["EDITION_ID"],
        "expert_id": row["EXPERT_ID"],
        "period_start": timestamp("PERIOD_START"),
        "period_end": timestamp("PERIOD_END"),
        "status": row["STATUS"],
        "subject": row["SUBJECT"],
        "output_language": row["OUTPUT_LANGUAGE"],
        "search": search,
        "selected_content_ids": list(row.get("SELECTED_CONTENT_IDS") or []),
        "dismissed_content_ids": list(row.get("DISMISSED_CONTENT_IDS") or []),
        "report_id": row.get("REPORT_ID"),
        "error": row.get("ERROR"),
        "created_at": timestamp("CREATED_AT"),
        "updated_at": timestamp("UPDATED_AT"),
    }


# ============================================================
# CLAIM A NEW OR FAILED EDITION
# ============================================================

def claim_touch_edition(
    edition_id: str,
    expert_id: str,
    period_start: datetime,
    period_end: datetime,
    subject: str,
    output_language: str,
) -> None:
    """Ready, reviewed and generated editions are never reset."""
    query_bq(
        f"""
        MERGE `{TABLE_TOUCH_EDITION}` AS target
        USING (SELECT @edition_id AS EDITION_ID) AS source
        ON target.EDITION_ID = source.EDITION_ID
        WHEN MATCHED AND target.STATUS = 'ERROR' THEN
          UPDATE SET
            STATUS = 'BUILDING',
            SUBJECT = @subject,
            OUTPUT_LANGUAGE = @output_language,
            ERROR = NULL,
            UPDATED_AT = CURRENT_TIMESTAMP()
        WHEN NOT MATCHED THEN
          INSERT (
            EDITION_ID, EXPERT_ID, PERIOD_START, PERIOD_END,
            STATUS, SUBJECT, OUTPUT_LANGUAGE, SEARCH_JSON,
            SELECTED_CONTENT_IDS, DISMISSED_CONTENT_IDS,
            REPORT_ID, ERROR, CREATED_AT, UPDATED_AT
          )
          VALUES (
            @edition_id, @expert_id,
            CAST(@period_start AS TIMESTAMP),
            CAST(@period_end AS TIMESTAMP),
            'BUILDING', @subject, @output_language, NULL,
            ARRAY<STRING>[], ARRAY<STRING>[],
            NULL, NULL, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()
          )
        """,
        {
            "edition_id": edition_id,
            "expert_id": expert_id,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "subject": subject,
            "output_language": output_language,
        },
    )


# ============================================================
# STORE PROPOSED CORPUS OR FAILURE
# ============================================================

def save_touch_edition_search(
    edition_id: str,
    search: dict,
) -> None:
    """No content is selected on the administrator's behalf."""
    query_bq(
        f"""
        UPDATE `{TABLE_TOUCH_EDITION}`
        SET
          STATUS = 'TO_REVIEW',
          SEARCH_JSON = PARSE_JSON(@search_json),
          ERROR = NULL,
          UPDATED_AT = CURRENT_TIMESTAMP()
        WHERE EDITION_ID = @edition_id
          AND STATUS = 'BUILDING'
        """,
        {
            "edition_id": edition_id,
            "search_json": json.dumps(search, ensure_ascii=False),
        },
    )


def record_touch_edition_error(
    edition_id: str,
    error: str,
) -> None:
    query_bq(
        f"""
        UPDATE `{TABLE_TOUCH_EDITION}`
        SET
          STATUS = 'ERROR',
          ERROR = @error,
          UPDATED_AT = CURRENT_TIMESTAMP()
        WHERE EDITION_ID = @edition_id
          AND STATUS = 'BUILDING'
        """,
        {"edition_id": edition_id, "error": error[:4000]},
    )
