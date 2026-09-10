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
    TABLE_OBSERVATION,
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
MAX_BACKFILL_LIMIT = 10


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

    # ========================================================
    # PROCESSING FILTER
    # ========================================================
    
    if retry_failed:
    
        # Retry only failures produced by the
        # current transformer version.
        processing_filter = """
        AND processing.STATUS = 'FAILED'
    
        AND processing.TRANSFORMER_VERSION = @version
        """
    
    else:
    
        # Standard backfill:
        # process new contents or contents produced
        # by an older transformer version.
        processing_filter = """
        AND (
            processing.ID_CONTENT IS NULL
    
            OR processing.TRANSFORMER_VERSION
               IS DISTINCT FROM @version
    
            OR (
                processing.TRANSFORMER_VERSION = @version
    
                AND processing.STATUS NOT IN (
                    'COMPLETED',
                    'FAILED',
                    'PROCESSING'
                )
            )
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

          {processing_filter}

        ORDER BY
            content.PUBLISHED_AT DESC,
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
# BACKFILL MONITORING
# ============================================================

def get_number_backfill_status() -> Dict[str, Any]:
    """
    Return the global Numbers transformation
    progress for the current transformer version.
    """

    rows = query_bq(
        f"""
        WITH source_contents AS (

            SELECT
                ID_CONTENT,
                ARRAY_LENGTH(
                    CHIFFRES
                ) AS RAW_NUMBERS_COUNT

            FROM `{TABLE_CONTENT_ENRICHED}`

            WHERE STATUS = 'PUBLISHED'

              AND IS_ACTIVE = TRUE

              AND PUBLISHED_AT IS NOT NULL

              AND CHIFFRES IS NOT NULL

              AND ARRAY_LENGTH(
                  CHIFFRES
              ) > 0
        ),

        content_status AS (

            SELECT

                source.ID_CONTENT,

                source.RAW_NUMBERS_COUNT,

                processing.STATUS,

                processing.TRANSFORMER_VERSION

            FROM source_contents source

            LEFT JOIN `{TABLE_PROCESSING}` processing
              ON processing.ID_CONTENT = source.ID_CONTENT
        ),

        content_totals AS (

            SELECT

                COUNT(*) AS TOTAL_CONTENTS,

                COALESCE(
                    SUM(RAW_NUMBERS_COUNT),
                    0
                ) AS TOTAL_RAW_NUMBERS,

                COUNTIF(
                    STATUS = 'COMPLETED'
                    AND TRANSFORMER_VERSION = @version
                ) AS COMPLETED_CONTENTS,

                COUNTIF(
                    STATUS = 'FAILED'
                    AND TRANSFORMER_VERSION = @version
                ) AS FAILED_CONTENTS,

                COUNTIF(
                    STATUS = 'PROCESSING'
                    AND TRANSFORMER_VERSION = @version
                ) AS PROCESSING_CONTENTS,

                COUNTIF(
                    STATUS IS NULL

                    OR TRANSFORMER_VERSION
                       IS DISTINCT FROM @version

                    OR (
                        TRANSFORMER_VERSION = @version
                        AND STATUS NOT IN (
                            'COMPLETED',
                            'FAILED',
                            'PROCESSING'
                        )
                    )
                ) AS PENDING_CONTENTS

            FROM content_status
        ),

        observation_totals AS (

            SELECT

                COUNT(*) AS TOTAL_OBSERVATIONS,

                COUNTIF(
                    STATUS = 'ACCEPTED'
                ) AS ACCEPTED_OBSERVATIONS,

                COUNTIF(
                    STATUS = 'REVIEW'
                ) AS REVIEW_OBSERVATIONS,

                COUNTIF(
                    STATUS = 'REJECTED'
                ) AS REJECTED_OBSERVATIONS

            FROM `{TABLE_OBSERVATION}`

            WHERE TRANSFORMER_VERSION = @version
        )

        SELECT

            content.TOTAL_CONTENTS,

            content.TOTAL_RAW_NUMBERS,

            content.COMPLETED_CONTENTS,

            content.FAILED_CONTENTS,

            content.PROCESSING_CONTENTS,

            content.PENDING_CONTENTS,

            observation.TOTAL_OBSERVATIONS,

            observation.ACCEPTED_OBSERVATIONS,

            observation.REVIEW_OBSERVATIONS,

            observation.REJECTED_OBSERVATIONS,

            ROUND(
                SAFE_DIVIDE(
                    content.COMPLETED_CONTENTS,
                    content.TOTAL_CONTENTS
                ) * 100,
                2
            ) AS PROGRESS_PERCENT

        FROM content_totals content

        CROSS JOIN observation_totals observation
        """,
        {
            "version": TRANSFORMER_VERSION,
        },
    ) or []

    if not rows:

        return {
            "transformer_version": (
                TRANSFORMER_VERSION
            ),
            "total_contents": 0,
            "total_raw_numbers": 0,
            "completed_contents": 0,
            "failed_contents": 0,
            "processing_contents": 0,
            "pending_contents": 0,
            "total_observations": 0,
            "accepted_observations": 0,
            "review_observations": 0,
            "rejected_observations": 0,
            "progress_percent": 0,
        }

    row = rows[0]

    return {
        "transformer_version": (
            TRANSFORMER_VERSION
        ),

        "total_contents": (
            row.get("TOTAL_CONTENTS")
            or 0
        ),

        "total_raw_numbers": (
            row.get("TOTAL_RAW_NUMBERS")
            or 0
        ),

        "completed_contents": (
            row.get("COMPLETED_CONTENTS")
            or 0
        ),

        "failed_contents": (
            row.get("FAILED_CONTENTS")
            or 0
        ),

        "processing_contents": (
            row.get("PROCESSING_CONTENTS")
            or 0
        ),

        "pending_contents": (
            row.get("PENDING_CONTENTS")
            or 0
        ),

        "total_observations": (
            row.get("TOTAL_OBSERVATIONS")
            or 0
        ),

        "accepted_observations": (
            row.get("ACCEPTED_OBSERVATIONS")
            or 0
        ),

        "review_observations": (
            row.get("REVIEW_OBSERVATIONS")
            or 0
        ),

        "rejected_observations": (
            row.get("REJECTED_OBSERVATIONS")
            or 0
        ),

        "progress_percent": (
            row.get("PROGRESS_PERCENT")
            or 0
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
