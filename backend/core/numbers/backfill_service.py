import json

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

from .transformer_models import (
    NumberTransformationResult,
)

from .transformer_service import (
    preview_content_numbers,
)

from .observation_repository import (
    TABLE_PROCESSING,
    TRANSFORMER_VERSION,
    replace_content_number_observations_batch,
)


# ============================================================
# TABLES
# ============================================================

TABLE_CONTENT_ENRICHED = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_CONTENT_ENRICHED"
)


# ============================================================
# CONFIG
# ============================================================

DEFAULT_BACKFILL_LIMIT = 5
MAX_BACKFILL_LIMIT = 25


# ============================================================
# LOAD NEXT CONTENT IDS
# ============================================================

def load_next_number_backfill_contents(
    limit: int = DEFAULT_BACKFILL_LIMIT,
    retry_failed: bool = False,
) -> list[str]:
    """
    Load the next published contents containing
    raw Numbers that have not yet been processed
    with the current transformer version.
    """

    safe_limit = max(
        1,
        min(
            int(limit),
            MAX_BACKFILL_LIMIT,
        ),
    )

    failed_filter = ""

    if not retry_failed:

        failed_filter = """
        AND NOT (
            processing.STATUS = 'FAILED'
            AND processing.TRANSFORMER_VERSION = @version
        )
        """

    rows = query_bq(
        f"""
        SELECT
            content.ID_CONTENT

        FROM `{TABLE_CONTENT_ENRICHED}` content

        LEFT JOIN `{TABLE_PROCESSING}` processing
          ON processing.ID_CONTENT = content.ID_CONTENT

        WHERE content.STATUS = 'PUBLISHED'

          AND content.IS_ACTIVE = TRUE

          AND content.PUBLISHED_AT IS NOT NULL

          AND content.CHIFFRES IS NOT NULL

          AND ARRAY_LENGTH(
              content.CHIFFRES
          ) > 0

          AND NOT (
              processing.STATUS = 'COMPLETED'
              AND processing.TRANSFORMER_VERSION = @version
          )

          {failed_filter}

        ORDER BY
            content.PUBLISHED_AT ASC,
            content.ID_CONTENT ASC

        LIMIT @limit
        """,
        {
            "version": TRANSFORMER_VERSION,
            "limit": safe_limit,
        },
    ) or []

    return [
        str(row["ID_CONTENT"])
        for row in rows
    ]


# ============================================================
# MARK BATCH STARTED
# ============================================================

def _mark_backfill_batch_started(
    content_ids: list[str],
):
    """
    Mark every content in one BigQuery MERGE.
    """

    if not content_ids:
        return

    payload = json.dumps([
        {
            "id_content": id_content,
        }
        for id_content in content_ids
    ])

    query_bq(
        f"""
        MERGE `{TABLE_PROCESSING}` target

        USING (

            SELECT
                JSON_VALUE(
                    item,
                    '$.id_content'
                ) AS ID_CONTENT

            FROM UNNEST(
                JSON_QUERY_ARRAY(@payload)
            ) item

        ) source

        ON target.ID_CONTENT = source.ID_CONTENT

        WHEN MATCHED THEN

          UPDATE SET

            STATUS = 'PROCESSING',

            ATTEMPT_COUNT = (
                COALESCE(
                    target.ATTEMPT_COUNT,
                    0
                ) + 1
            ),

            ERROR = NULL,

            TRANSFORMER_VERSION = @version,

            STARTED_AT = CURRENT_TIMESTAMP(),

            COMPLETED_AT = NULL,

            UPDATED_AT = CURRENT_TIMESTAMP()

        WHEN NOT MATCHED THEN

          INSERT (

            ID_CONTENT,

            STATUS,

            RAW_NUMBERS_COUNT,

            ACCEPTED_COUNT,

            REJECTED_COUNT,

            REVIEW_COUNT,

            ATTEMPT_COUNT,

            ERROR,

            TRANSFORMER_VERSION,

            STARTED_AT,

            COMPLETED_AT,

            UPDATED_AT

          )

          VALUES (

            source.ID_CONTENT,

            'PROCESSING',

            0,

            0,

            0,

            0,

            1,

            NULL,

            @version,

            CURRENT_TIMESTAMP(),

            NULL,

            CURRENT_TIMESTAMP()

          )
        """,
        {
            "payload": payload,
            "version": TRANSFORMER_VERSION,
        },
    )


# ============================================================
# MARK BATCH FINISHED
# ============================================================

def _mark_backfill_batch_finished(
    results: list[NumberTransformationResult],
    failures: list[Dict[str, str]],
):
    """
    Write successful and failed processing statuses
    using one BigQuery MERGE.
    """

    status_rows = []

    for result in results:

        status_rows.append({
            "id_content": result.id_content,
            "status": "COMPLETED",
            "raw_numbers_count": (
                result.raw_numbers_count
            ),
            "accepted_count": (
                result.accepted_count
            ),
            "rejected_count": (
                result.rejected_count
            ),
            "review_count": (
                result.review_count
            ),
            "error": None,
        })

    for failure in failures:

        status_rows.append({
            "id_content": failure["id_content"],
            "status": "FAILED",
            "raw_numbers_count": 0,
            "accepted_count": 0,
            "rejected_count": 0,
            "review_count": 0,
            "error": failure["error"][:5000],
        })

    if not status_rows:
        return

    payload = json.dumps(
        status_rows
    )

    query_bq(
        f"""
        MERGE `{TABLE_PROCESSING}` target

        USING (

            SELECT

                JSON_VALUE(
                    item,
                    '$.id_content'
                ) AS ID_CONTENT,

                JSON_VALUE(
                    item,
                    '$.status'
                ) AS STATUS,

                SAFE_CAST(
                    JSON_VALUE(
                        item,
                        '$.raw_numbers_count'
                    )
                    AS INT64
                ) AS RAW_NUMBERS_COUNT,

                SAFE_CAST(
                    JSON_VALUE(
                        item,
                        '$.accepted_count'
                    )
                    AS INT64
                ) AS ACCEPTED_COUNT,

                SAFE_CAST(
                    JSON_VALUE(
                        item,
                        '$.rejected_count'
                    )
                    AS INT64
                ) AS REJECTED_COUNT,

                SAFE_CAST(
                    JSON_VALUE(
                        item,
                        '$.review_count'
                    )
                    AS INT64
                ) AS REVIEW_COUNT,

                JSON_VALUE(
                    item,
                    '$.error'
                ) AS ERROR

            FROM UNNEST(
                JSON_QUERY_ARRAY(@payload)
            ) item

        ) source

        ON target.ID_CONTENT = source.ID_CONTENT

        WHEN MATCHED THEN

          UPDATE SET

            STATUS = source.STATUS,

            RAW_NUMBERS_COUNT = (
                source.RAW_NUMBERS_COUNT
            ),

            ACCEPTED_COUNT = (
                source.ACCEPTED_COUNT
            ),

            REJECTED_COUNT = (
                source.REJECTED_COUNT
            ),

            REVIEW_COUNT = (
                source.REVIEW_COUNT
            ),

            ERROR = source.ERROR,

            TRANSFORMER_VERSION = @version,

            COMPLETED_AT = CURRENT_TIMESTAMP(),

            UPDATED_AT = CURRENT_TIMESTAMP()

        WHEN NOT MATCHED THEN

          INSERT (

            ID_CONTENT,

            STATUS,

            RAW_NUMBERS_COUNT,

            ACCEPTED_COUNT,

            REJECTED_COUNT,

            REVIEW_COUNT,

            ATTEMPT_COUNT,

            ERROR,

            TRANSFORMER_VERSION,

            STARTED_AT,

            COMPLETED_AT,

            UPDATED_AT

          )

          VALUES (

            source.ID_CONTENT,

            source.STATUS,

            source.RAW_NUMBERS_COUNT,

            source.ACCEPTED_COUNT,

            source.REJECTED_COUNT,

            source.REVIEW_COUNT,

            1,

            source.ERROR,

            @version,

            CURRENT_TIMESTAMP(),

            CURRENT_TIMESTAMP(),

            CURRENT_TIMESTAMP()

          )
        """,
        {
            "payload": payload,
            "version": TRANSFORMER_VERSION,
        },
    )


# ============================================================
# SERIALIZATION
# ============================================================

def _serialize_result(
    result: NumberTransformationResult,
) -> Dict[str, Any]:

    return {
        "id_content": result.id_content,

        "title": result.title,

        "published_at": (
            result.published_at.isoformat()
            if result.published_at
            else None
        ),

        "raw_numbers_count": (
            result.raw_numbers_count
        ),

        "accepted_count": (
            result.accepted_count
        ),

        "rejected_count": (
            result.rejected_count
        ),

        "review_count": (
            result.review_count
        ),
    }


# ============================================================
# RUN BACKFILL BATCH
# ============================================================

def run_number_backfill_batch(
    limit: int = DEFAULT_BACKFILL_LIMIT,
    retry_failed: bool = False,
) -> Dict[str, Any]:
    """
    Transform and persist the next batch of
    existing content Numbers.

    LLM transformations are executed one content
    at a time, while BigQuery persistence is
    grouped for the complete batch.
    """

    content_ids = (
        load_next_number_backfill_contents(
            limit=limit,
            retry_failed=retry_failed,
        )
    )

    if not content_ids:

        return {
            "status": "completed",
            "transformer_version": (
                TRANSFORMER_VERSION
            ),
            "selected_count": 0,
            "processed_count": 0,
            "failed_count": 0,
            "storage": {
                "contents_processed": 0,
                "observations_saved": 0,
                "relations_saved": 0,
            },
            "results": [],
            "failures": [],
        }

    _mark_backfill_batch_started(
        content_ids=content_ids,
    )

    results: list[
        NumberTransformationResult
    ] = []

    failures: list[
        Dict[str, str]
    ] = []

    # ========================================================
    # TRANSFORM IN MEMORY
    # ========================================================

    for id_content in content_ids:

        try:

            result = preview_content_numbers(
                id_content=id_content,
            )

            results.append(
                result
            )

        except Exception as error:

            failures.append({
                "id_content": id_content,
                "error": str(error),
            })

    # ========================================================
    # GROUPED STORAGE
    # ========================================================

    storage = {
        "contents_processed": 0,
        "observations_saved": 0,
        "relations_saved": 0,
    }

    if results:

        try:

            storage = (
                replace_content_number_observations_batch(
                    results=results,
                )
            )

        except Exception as storage_error:

            error_message = (
                "Batch storage failed: "
                f"{storage_error}"
            )

            for result in results:

                failures.append({
                    "id_content": (
                        result.id_content
                    ),
                    "error": error_message,
                })

            results = []

    # ========================================================
    # GROUPED MONITORING
    # ========================================================

    _mark_backfill_batch_finished(
        results=results,
        failures=failures,
    )

    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "status": (
            "partial"
            if failures
            else "processed"
        ),

        "transformer_version": (
            TRANSFORMER_VERSION
        ),

        "selected_count": len(
            content_ids
        ),

        "processed_count": len(
            results
        ),

        "failed_count": len(
            failures
        ),

        "storage": storage,

        "results": [
            _serialize_result(result)
            for result in results
        ],

        "failures": failures,
    }
