import argparse

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
# LOAD CONTENTS TO PROCESS
# ============================================================

def load_contents(
    limit: int,
) -> List[Dict]:

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

            FROM `{TABLE_BACKLOG}` b

            WHERE
                b.ID_CONTENT = c.ID_CONTENT
                AND b.STATUS = 'COMPLETED'
        )

    ORDER BY
        c.PUBLISHED_AT DESC

    LIMIT @limit
    """

    return query_bq(
        sql,
        {
            "translation_start_date":
                TRANSLATION_START_DATE,

            "limit":
                limit,
        },
    )


# ============================================================
# BUILD TRANSLATION PAYLOAD
# ============================================================

def build_payload(
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
# RESULT ROW
# ============================================================

def build_result_row(
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

def translate_one_content(
    content: Dict,
) -> Dict:

    content_id = content[
        "ID_CONTENT"
    ]

    try:

        payload = build_payload(
            content
        )

        if not payload:

            return build_result_row(
                content_id=content_id,
                status="COMPLETED",
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

        return build_result_row(

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

        return build_result_row(

            content_id=
                content_id,

            status=
                "FAILED",

            error=
                error_message[:5000],
        )


# ============================================================
# WRITE STAGING BATCH
# ============================================================

def write_staging_batch(
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
# RUN BACKFILL
# ============================================================

def run_backfill(
    limit: int,
    workers: int,
    write_batch_size: int,
) -> Dict:

    contents = load_contents(
        limit=limit
    )

    selected_count = len(
        contents
    )

    print(
        "=================================================="
    )

    print(
        "TRANSLATION BACKFILL"
    )

    print(
        "Dataset:",
        f"{BQ_PROJECT}.{BQ_DATASET}",
    )

    print(
        "Selected contents:",
        selected_count,
    )

    print(
        "Workers:",
        workers,
    )

    print(
        "Write batch size:",
        write_batch_size,
    )

    print(
        "=================================================="
    )

    if not contents:

        return {

            "selected_count":
                0,

            "completed_count":
                0,

            "failed_count":
                0,
        }

    completed_count = 0
    failed_count = 0
    processed_count = 0

    pending_rows = []

    # ========================================================
    # PARALLEL TRANSLATION
    # ========================================================

    with ThreadPoolExecutor(
        max_workers=workers
    ) as executor:

        futures = {

            executor.submit(
                translate_one_content,
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

                result_row = build_result_row(

                    content_id=
                        content_id,

                    status=
                        "FAILED",

                    error=
                        str(error)[:5000],
                )

            processed_count += 1

            if (
                result_row["STATUS"]
                == "COMPLETED"
            ):

                completed_count += 1

                marker = "✔"

            else:

                failed_count += 1

                marker = "❌"

            pending_rows.append(
                result_row
            )

            print(
                marker,
                f"{processed_count}/{selected_count}",
                content_id,
                result_row["STATUS"],
            )

            # =================================================
            # PERIODIC WRITE
            # =================================================

            if (
                len(pending_rows)
                >= write_batch_size
            ):

                write_staging_batch(
                    pending_rows
                )

                print(
                    "💾 Staging rows written:",
                    len(pending_rows),
                )

                pending_rows = []

    # ========================================================
    # FINAL WRITE
    # ========================================================

    if pending_rows:

        write_staging_batch(
            pending_rows
        )

        print(
            "💾 Final staging rows written:",
            len(pending_rows),
        )

    result = {

        "selected_count":
            selected_count,

        "completed_count":
            completed_count,

        "failed_count":
            failed_count,
    }

    print(
        "=================================================="
    )

    print(
        "BACKFILL FINISHED:",
        result,
    )

    print(
        "=================================================="
    )

    return result


# ============================================================
# COMMAND LINE
# ============================================================

def parse_args():

    parser = argparse.ArgumentParser(

        description=(
            "Translate 2026+ content fields "
            "into English staging."
        )
    )

    parser.add_argument(

        "--limit",

        type=int,

        default=100,

        help=(
            "Maximum number of contents "
            "processed during this run."
        ),
    )

    parser.add_argument(

        "--workers",

        type=int,

        default=5,

        help=(
            "Number of simultaneous LLM calls."
        ),
    )

    parser.add_argument(

        "--write-batch-size",

        type=int,

        default=50,

        help=(
            "Number of results written "
            "per BigQuery load job."
        ),
    )

    return parser.parse_args()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    args = parse_args()

    run_backfill(

        limit=
            args.limit,

        workers=
            args.workers,

        write_batch_size=
            args.write_batch_size,
    )
