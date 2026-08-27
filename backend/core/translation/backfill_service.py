import threading

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)

from datetime import (
    datetime,
    timezone,
)

from typing import (
    Dict,
    List,
    Optional,
)

from google.cloud import bigquery

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
    get_bigquery_client,
)

from core.translation.drawer_translation_service import (
    translate_fields,
)


# ============================================================
# TABLES
# ============================================================

TABLE_CONTENT = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"
)

TABLE_BACKLOG = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_CONTENT_TRANSLATION_BACKLOG"
)


# ============================================================
# CONFIG
# ============================================================

TARGET_LANG = "en"

TRANSLATION_START_DATE = (
    "2026-01-01 00:00:00+00"
)

CHUNK_SIZE = 100

WORKERS = 5

WRITE_BATCH_SIZE = 25

MAX_ATTEMPTS = 3


# ============================================================
# FIELD MAPPING
# ============================================================

FIELD_MAPPING = {

    "CONTENT_BODY": {
        "target":
            "CONTENT_BODY_EN",
    },

    "SIGNAL_ANALYTIQUE": {
        "target":
            "SIGNAL_ANALYTIQUE_EN",
    },

    "MECANIQUE_EXPLIQUEE": {
        "target":
            "MECANIQUE_EXPLIQUEE_EN",
    },

    "ENJEU_STRATEGIQUE": {
        "target":
            "ENJEU_STRATEGIQUE_EN",
    },

    "POINT_DE_FRICTION": {
        "target":
            "POINT_DE_FRICTION_EN",
    },
}


# ============================================================
# RUNTIME STATE
# ============================================================

_STATE_LOCK = (
    threading.Lock()
)

_RUNNING = False

_STARTED_AT = None

_FINISHED_AT = None

_LAST_ERROR = None


# ============================================================
# RESERVE BACKFILL
# ============================================================

def reserve_translation_backfill() -> bool:

    global _RUNNING
    global _STARTED_AT
    global _FINISHED_AT
    global _LAST_ERROR

    with _STATE_LOCK:

        if _RUNNING:
            return False

        _RUNNING = True

        _STARTED_AT = datetime.now(
            timezone.utc
        )

        _FINISHED_AT = None

        _LAST_ERROR = None

        return True


# ============================================================
# LOAD NEXT CHUNK
# ============================================================

def _load_next_chunk() -> List[Dict]:

    missing_conditions = []

    for source_col, config in (
        FIELD_MAPPING.items()
    ):

        target_col = config[
            "target"
        ]

        missing_conditions.append(
            f"""
            (
                c.{source_col} IS NOT NULL
                AND TRIM(c.{source_col}) != ''
                AND (
                    c.{target_col} IS NULL
                    OR TRIM(c.{target_col}) = ''
                )
            )
            """
        )

    sql = f"""
    SELECT

        c.ID_CONTENT,

        c.CONTENT_BODY,
        c.CONTENT_BODY_EN,

        c.SIGNAL_ANALYTIQUE,
        c.SIGNAL_ANALYTIQUE_EN,

        c.MECANIQUE_EXPLIQUEE,
        c.MECANIQUE_EXPLIQUEE_EN,

        c.ENJEU_STRATEGIQUE,
        c.ENJEU_STRATEGIQUE_EN,

        c.POINT_DE_FRICTION,
        c.POINT_DE_FRICTION_EN

    FROM `{TABLE_CONTENT}` c

    WHERE

        c.STATUS = 'PUBLISHED'

        AND c.IS_ACTIVE = TRUE

        AND c.PUBLISHED_AT >= TIMESTAMP(
            @translation_start_date
        )

        AND (
            {" OR ".join(missing_conditions)}
        )

        AND NOT EXISTS (

            SELECT 1

            FROM `{TABLE_BACKLOG}` completed

            WHERE
                completed.ID_CONTENT
                    = c.ID_CONTENT

                AND completed.STATUS
                    = 'COMPLETED'
        )

        AND (

            SELECT COUNTIF(
                failed.STATUS = 'FAILED'
            )

            FROM `{TABLE_BACKLOG}` failed

            WHERE
                failed.ID_CONTENT
                    = c.ID_CONTENT

        ) < @max_attempts

    ORDER BY
        c.PUBLISHED_AT DESC

    LIMIT @chunk_size
    """

    return query_bq(
        sql,
        {
            "translation_start_date":
                TRANSLATION_START_DATE,

            "max_attempts":
                MAX_ATTEMPTS,

            "chunk_size":
                CHUNK_SIZE,
        },
    )


# ============================================================
# BUILD PAYLOAD
# ============================================================

def _build_payload(
    content: Dict,
) -> Dict[str, str]:

    payload = {}

    for source_col, config in (
        FIELD_MAPPING.items()
    ):

        target_col = config[
            "target"
        ]

        source_value = (
            content.get(
                source_col
            )
            or ""
        ).strip()

        target_value = (
            content.get(
                target_col
            )
            or ""
        ).strip()

        if not source_value:
            continue

        if target_value:
            continue

        payload[
            target_col
        ] = source_value

    return payload


# ============================================================
# BUILD STAGING ROW
# ============================================================

def _build_staging_row(
    content_id: str,
    status: str,
    translated: Optional[Dict] = None,
    error: Optional[str] = None,
) -> Dict:

    translated = (
        translated
        or {}
    )

    return {

        "ID_CONTENT":
            content_id,

        "CONTENT_BODY_EN":
            translated.get(
                "CONTENT_BODY_EN"
            ),

        "SIGNAL_ANALYTIQUE_EN":
            translated.get(
                "SIGNAL_ANALYTIQUE_EN"
            ),

        "MECANIQUE_EXPLIQUEE_EN":
            translated.get(
                "MECANIQUE_EXPLIQUEE_EN"
            ),

        "ENJEU_STRATEGIQUE_EN":
            translated.get(
                "ENJEU_STRATEGIQUE_EN"
            ),

        "POINT_DE_FRICTION_EN":
            translated.get(
                "POINT_DE_FRICTION_EN"
            ),

        "STATUS":
            status,

        "ERROR":
            error,

        "CREATED_AT":
            datetime.now(
                timezone.utc
            ),
    }


# ============================================================
# TRANSLATE ONE CONTENT
# ============================================================

def _translate_one_content(
    content: Dict,
) -> Dict:

    content_id = content[
        "ID_CONTENT"
    ]

    try:

        payload = _build_payload(
            content
        )

        if not payload:

            return _build_staging_row(

                content_id=
                    content_id,

                status=
                    "COMPLETED",
            )

        # ====================================================
        # ONE LLM CALL FOR ALL MISSING FIELDS
        # ====================================================

        translated = translate_fields(

            fields=
                payload,

            target_lang=
                TARGET_LANG,

            raise_on_error=
                True,
        )

        return _build_staging_row(

            content_id=
                content_id,

            status=
                "COMPLETED",

            translated=
                translated,
        )

    except Exception as error:

        error_message = (
            str(error)
            or error.__class__.__name__
        )

        return _build_staging_row(

            content_id=
                content_id,

            status=
                "FAILED",

            error=
                error_message[:5000],
        )


# ============================================================
# WRITE STAGING ROWS
# ============================================================

def _write_staging_rows(
    rows: List[Dict],
):

    if not rows:
        return

    client = get_bigquery_client()

    job_config = (
        bigquery.LoadJobConfig(

            write_disposition=(
                bigquery.WriteDisposition.WRITE_APPEND
            ),
        )
    )

    client.load_table_from_json(

        rows,

        TABLE_BACKLOG,

        job_config=
            job_config,

    ).result()


# ============================================================
# PROCESS CHUNK
# ============================================================

def _process_chunk(
    contents: List[Dict],
) -> Dict:

    completed_count = 0

    failed_count = 0

    processed_count = 0

    pending_rows = []

    with ThreadPoolExecutor(
        max_workers=WORKERS
    ) as executor:

        futures = {

            executor.submit(
                _translate_one_content,
                content,
            ):
                content["ID_CONTENT"]

            for content in contents
        }

        for future in as_completed(
            futures
        ):

            content_id = (
                futures[
                    future
                ]
            )

            try:

                result_row = (
                    future.result()
                )

            except Exception as error:

                result_row = (
                    _build_staging_row(

                        content_id=
                            content_id,

                        status=
                            "FAILED",

                        error=
                            str(error)[:5000],
                    )
                )

            processed_count += 1

            if (
                result_row["STATUS"]
                == "COMPLETED"
            ):

                completed_count += 1

            else:

                failed_count += 1

            pending_rows.append(
                result_row
            )

            # =================================================
            # PERIODIC WRITE
            # =================================================

            if (
                len(pending_rows)
                >= WRITE_BATCH_SIZE
            ):

                _write_staging_rows(
                    pending_rows
                )

                pending_rows = []

            if (
                processed_count % 10
                == 0
            ):

                print(
                    "TRANSLATION BACKFILL:",
                    processed_count,
                    "/",
                    len(contents),
                )

    # ========================================================
    # FINAL WRITE
    # ========================================================

    if pending_rows:

        _write_staging_rows(
            pending_rows
        )

    return {

        "completed_count":
            completed_count,

        "failed_count":
            failed_count,
    }


# ============================================================
# RUN BACKFILL
# ============================================================

def run_translation_backfill():

    global _RUNNING
    global _FINISHED_AT
    global _LAST_ERROR

    total_completed = 0

    total_failed = 0

    try:

        print(
            "=================================================="
        )

        print(
            "TRANSLATION BACKFILL STARTED"
        )

        print(
            "Dataset:",
            f"{BQ_PROJECT}.{BQ_DATASET}",
        )

        print(
            "Start date:",
            TRANSLATION_START_DATE,
        )

        print(
            "=================================================="
        )

        while True:

            contents = (
                _load_next_chunk()
            )

            if not contents:
                break

            result = _process_chunk(
                contents
            )

            total_completed += (
                result[
                    "completed_count"
                ]
            )

            total_failed += (
                result[
                    "failed_count"
                ]
            )

            print(
                "BACKFILL TOTAL:",
                {
                    "completed":
                        total_completed,

                    "failed":
                        total_failed,
                },
            )

        print(
            "=================================================="
        )

        print(
            "TRANSLATION BACKFILL FINISHED"
        )

        print(
            {
                "completed":
                    total_completed,

                "failed":
                    total_failed,
            },
        )

        print(
            "=================================================="
        )

    except Exception as error:

        _LAST_ERROR = (
            str(error)
            or error.__class__.__name__
        )

        print(
            "❌ TRANSLATION BACKFILL ERROR:",
            _LAST_ERROR,
        )

    finally:

        with _STATE_LOCK:

            _RUNNING = False

            _FINISHED_AT = (
                datetime.now(
                    timezone.utc
                )
            )


# ============================================================
# PERSISTED PROGRESS
# ============================================================

def _get_persisted_progress() -> Dict:

    missing_conditions = []

    for source_col, config in (
        FIELD_MAPPING.items()
    ):

        target_col = config[
            "target"
        ]

        missing_conditions.append(
            f"""
            (
                c.{source_col} IS NOT NULL
                AND TRIM(c.{source_col}) != ''
                AND (
                    c.{target_col} IS NULL
                    OR TRIM(c.{target_col}) = ''
                )
            )
            """
        )

    rows = query_bq(
        f"""
        WITH eligible AS (

            SELECT
                c.ID_CONTENT

            FROM `{TABLE_CONTENT}` c

            WHERE
                c.STATUS = 'PUBLISHED'

                AND c.IS_ACTIVE = TRUE

                AND c.PUBLISHED_AT >= TIMESTAMP(
                    @translation_start_date
                )

                AND (
                    {" OR ".join(missing_conditions)}
                )
        ),

        attempts AS (

            SELECT

                ID_CONTENT,

                COUNTIF(
                    STATUS = 'COMPLETED'
                ) AS completed_attempts,

                COUNTIF(
                    STATUS = 'FAILED'
                ) AS failed_attempts

            FROM `{TABLE_BACKLOG}`

            GROUP BY
                ID_CONTENT
        )

        SELECT

            COUNT(*) AS total_count,

            COUNTIF(
                COALESCE(
                    a.completed_attempts,
                    0
                ) > 0
            ) AS completed_count,

            COUNTIF(
                COALESCE(
                    a.completed_attempts,
                    0
                ) = 0

                AND COALESCE(
                    a.failed_attempts,
                    0
                ) >= @max_attempts
            ) AS failed_count,

            COALESCE(
                SUM(
                    a.failed_attempts
                ),
                0
            ) AS failed_attempt_count

        FROM eligible e

        LEFT JOIN attempts a
          ON a.ID_CONTENT = e.ID_CONTENT
        """,
        {
            "translation_start_date":
                TRANSLATION_START_DATE,

            "max_attempts":
                MAX_ATTEMPTS,
        },
    )

    if not rows:

        return {

            "total_count":
                0,

            "completed_count":
                0,

            "failed_count":
                0,

            "failed_attempt_count":
                0,

            "remaining_count":
                0,

            "progress_percent":
                0,
        }

    row = rows[0]

    total_count = int(
        row.get(
            "total_count"
        )
        or 0
    )

    completed_count = int(
        row.get(
            "completed_count"
        )
        or 0
    )

    failed_count = int(
        row.get(
            "failed_count"
        )
        or 0
    )

    failed_attempt_count = int(
        row.get(
            "failed_attempt_count"
        )
        or 0
    )

    remaining_count = max(

        total_count
        - completed_count
        - failed_count,

        0,
    )

    progress_percent = (

        round(
            (
                completed_count
                / total_count
            )
            * 100,
            1,
        )

        if total_count
        else 0
    )

    return {

        "total_count":
            total_count,

        "completed_count":
            completed_count,

        "failed_count":
            failed_count,

        "failed_attempt_count":
            failed_attempt_count,

        "remaining_count":
            remaining_count,

        "progress_percent":
            progress_percent,
    }


# ============================================================
# PUBLIC STATUS
# ============================================================

def get_translation_backfill_status() -> Dict:

    with _STATE_LOCK:

        running = _RUNNING

        started_at = _STARTED_AT

        finished_at = _FINISHED_AT

        last_error = _LAST_ERROR

    progress = (
        _get_persisted_progress()
    )

    if running:

        state = "RUNNING"

    elif last_error:

        state = "FAILED"

    elif (
        progress["total_count"] > 0
        and progress["remaining_count"] == 0
        and progress["failed_count"] == 0
    ):

        state = "READY_TO_MERGE"

    elif progress["completed_count"] > 0:

        state = "PAUSED"

    else:

        state = "NOT_STARTED"

    return {

        "state":
            state,

        "running":
            running,

        "started_at": (
            started_at.isoformat()
            if started_at
            else None
        ),

        "finished_at": (
            finished_at.isoformat()
            if finished_at
            else None
        ),

        "last_error":
            last_error,

        **progress,
    }
