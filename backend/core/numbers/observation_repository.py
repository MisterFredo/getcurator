import hashlib
import uuid

from datetime import (
    datetime,
    timezone,
)

from typing import (
    Any,
    Dict,
)

from google.cloud import bigquery

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    get_bigquery_client,
    query_bq,
)

from .transformer_models import (
    NumberTransformationResult,
)


# ============================================================
# TABLES
# ============================================================

TABLE_OBSERVATION = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_NUMBER_OBSERVATION"
)

TABLE_OBSERVATION_ENTITY = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_NUMBER_OBSERVATION_ENTITY"
)

TABLE_PROCESSING = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_NUMBER_PROCESSING"
)


# ============================================================
# CONFIG
# ============================================================

TRANSFORMER_VERSION = "numbers-v1"


# ============================================================
# HELPERS
# ============================================================

def _now() -> str:

    return datetime.now(
        timezone.utc,
    ).isoformat()


def _raw_hash(
    id_content: str,
    raw_line: str,
) -> str:

    value = (
        f"{id_content}\n{raw_line}"
    )

    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def _number_id(
    raw_hash: str,
) -> str:
    """
    Produce a stable Number identifier.

    The same content/raw-line pair always
    produces the same identifier.
    """

    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            (
                "getcurator:number-observation:"
                f"{raw_hash}"
            ),
        )
    )


# ============================================================
# PROCESSING STATUS
# ============================================================

def mark_number_processing_started(
    id_content: str,
):

    query_bq(
        f"""
        MERGE `{TABLE_PROCESSING}` target

        USING (
            SELECT
                @id_content AS ID_CONTENT
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
            @id_content,
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
            "id_content": id_content,
            "version": TRANSFORMER_VERSION,
        },
    )


def mark_number_processing_completed(
    result: NumberTransformationResult,
):

    query_bq(
        f"""
        UPDATE `{TABLE_PROCESSING}`

        SET
          STATUS = 'COMPLETED',
          RAW_NUMBERS_COUNT = @raw_count,
          ACCEPTED_COUNT = @accepted_count,
          REJECTED_COUNT = @rejected_count,
          REVIEW_COUNT = @review_count,
          ERROR = NULL,
          TRANSFORMER_VERSION = @version,
          COMPLETED_AT = CURRENT_TIMESTAMP(),
          UPDATED_AT = CURRENT_TIMESTAMP()

        WHERE ID_CONTENT = @id_content
        """,
        {
            "id_content": result.id_content,
            "raw_count": (
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
            "version": TRANSFORMER_VERSION,
        },
    )


def mark_number_processing_failed(
    id_content: str,
    error: str,
):

    query_bq(
        f"""
        UPDATE `{TABLE_PROCESSING}`

        SET
          STATUS = 'FAILED',
          ERROR = @error,
          TRANSFORMER_VERSION = @version,
          COMPLETED_AT = CURRENT_TIMESTAMP(),
          UPDATED_AT = CURRENT_TIMESTAMP()

        WHERE ID_CONTENT = @id_content
        """,
        {
            "id_content": id_content,
            "error": str(error)[:5000],
            "version": TRANSFORMER_VERSION,
        },
    )


# ============================================================
# BUILD STORAGE ROWS
# ============================================================

def _build_storage_rows(
    result: NumberTransformationResult,
):

    now = _now()

    # Dictionaries provide an additional
    # deterministic deduplication layer.
    observation_rows: Dict[
        str,
        Dict[str, Any],
    ] = {}

    relation_rows: Dict[
        tuple[str, str, str],
        Dict[str, Any],
    ] = {}

    for number in result.numbers:

        raw_hash = _raw_hash(
            id_content=result.id_content,
            raw_line=number.raw_line,
        )

        id_number = _number_id(
            raw_hash=raw_hash,
        )

        observation_rows[
            id_number
        ] = {
            "ID_NUMBER": id_number,
            "ID_CONTENT": result.id_content,

            "RAW_LINE": number.raw_line,
            "RAW_HASH": raw_hash,

            "LABEL": number.label,
            "METRIC_TYPE": (
                number.metric_type
            ),

            "VALUE": number.value,
            "VALUE_MIN": number.value_min,
            "VALUE_MAX": number.value_max,

            "UNIT": number.unit,
            "SCALE": number.scale,

            "ZONE": number.zone,
            "PERIOD_LABEL": (
                number.period_label
            ),
            "VALUE_STATUS": (
                number.value_status
            ),

            "STATUS": number.status,
            "CONFIDENCE": (
                number.confidence
            ),
            "REASON": number.reason,

            "PUBLISHED_AT": (
                result.published_at.isoformat()
                if result.published_at
                else None
            ),

            "TRANSFORMER_VERSION": (
                TRANSFORMER_VERSION
            ),

            "CREATED_AT": now,
            "UPDATED_AT": now,
        }

        for entity in number.entities:

            relation_key = (
                id_number,
                entity.entity_type,
                entity.entity_id,
            )

            relation_rows[
                relation_key
            ] = {
                "ID_NUMBER": id_number,

                "ENTITY_TYPE": (
                    entity.entity_type
                ),

                "ENTITY_ID": (
                    entity.entity_id
                ),

                "ENTITY_LABEL": (
                    entity.entity_label
                ),

                "CREATED_AT": now,
            }

    return (
        list(
            observation_rows.values()
        ),
        list(
            relation_rows.values()
        ),
    )


# ============================================================
# REPLACE CONTENT OBSERVATIONS
# ============================================================

def replace_content_number_observations(
    result: NumberTransformationResult,
):
    """
    Replace every transformed Number associated
    with one content.

    This function is intended for individual
    processing and validation.

    Historical bulk processing will use a
    dedicated batch implementation.
    """

    observation_rows, relation_rows = (
        _build_storage_rows(
            result=result,
        )
    )

    client = get_bigquery_client()

    # ========================================================
    # DELETE PREVIOUS RELATIONS
    # ========================================================

    query_bq(
        f"""
        DELETE FROM `{TABLE_OBSERVATION_ENTITY}`

        WHERE ID_NUMBER IN (

            SELECT ID_NUMBER

            FROM `{TABLE_OBSERVATION}`

            WHERE ID_CONTENT = @id_content
        )
        """,
        {
            "id_content": result.id_content,
        },
    )

    # ========================================================
    # DELETE PREVIOUS OBSERVATIONS
    # ========================================================

    query_bq(
        f"""
        DELETE FROM `{TABLE_OBSERVATION}`

        WHERE ID_CONTENT = @id_content
        """,
        {
            "id_content": result.id_content,
        },
    )

    # ========================================================
    # INSERT OBSERVATIONS
    # ========================================================

    if observation_rows:

        client.load_table_from_json(
            observation_rows,
            TABLE_OBSERVATION,
            job_config=(
                bigquery.LoadJobConfig(
                    write_disposition=(
                        "WRITE_APPEND"
                    )
                )
            ),
        ).result()

    # ========================================================
    # INSERT RELATIONS
    # ========================================================

    if relation_rows:

        client.load_table_from_json(
            relation_rows,
            TABLE_OBSERVATION_ENTITY,
            job_config=(
                bigquery.LoadJobConfig(
                    write_disposition=(
                        "WRITE_APPEND"
                    )
                )
            ),
        ).result()

    return {
        "id_content": result.id_content,

        "observations_saved": len(
            observation_rows
        ),

        "relations_saved": len(
            relation_rows
        ),
    }
