# backend/core/digest/repository.py

from datetime import datetime

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
    update_bq,
    get_bigquery_client,
)

from google.cloud import bigquery

from core.digest.models import (
    DigestBatch,
    DigestBatchItem,
)

# ============================================================
# TABLES
# ============================================================

TABLE_BATCH = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_DIGEST_BATCH"
)

TABLE_ITEM = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_DIGEST_BATCH_ITEM"
)

# ============================================================
# MAPPING
# ============================================================

def _map_batch(
    row,
) -> DigestBatch:

    return DigestBatch(

        id=row["ID"],

        frequency=row["FREQUENCY"],

        audience=row["AUDIENCE"],

        period_start=row["PERIOD_START"],

        period_end=row["PERIOD_END"],

        status=row["STATUS"],

        items_count=row["ITEMS_COUNT"],

        generated_count=row["GENERATED_COUNT"],

        sent_count=row["SENT_COUNT"],

        failed_count=row["FAILED_COUNT"],

        created_at=row["CREATED_AT"],

        completed_at=row.get("COMPLETED_AT"),

    )


def _map_batch_item(
    row,
) -> DigestBatchItem:

    return DigestBatchItem(

        id=row["ID"],

        batch_id=row["BATCH_ID"],

        user_id=row["USER_ID"],

        review_id=row.get("REVIEW_ID"),

        status=row["STATUS"],

        selected_contents=row["SELECTED_CONTENTS"],

        generated_at=row.get("GENERATED_AT"),

        sent_at=row.get("SENT_AT"),

        error=row.get("ERROR"),

    )

# ============================================================
# BATCH
# ============================================================

def insert_batch(
    batch: DigestBatch,
) -> DigestBatch:
    """
    Persist a new DigestBatch.
    """

    client = get_bigquery_client()

    row = [{

        "ID": batch.id,

        "FREQUENCY": batch.frequency,

        "AUDIENCE": batch.audience,

        "PERIOD_START": batch.period_start.isoformat(),

        "PERIOD_END": batch.period_end.isoformat(),

        "STATUS": batch.status,

        "ITEMS_COUNT": batch.items_count,

        "GENERATED_COUNT": batch.generated_count,

        "SENT_COUNT": batch.sent_count,

        "FAILED_COUNT": batch.failed_count,

        "CREATED_AT": batch.created_at.isoformat(),

        "COMPLETED_AT": (
            batch.completed_at.isoformat()
            if batch.completed_at
            else None
        ),

    }]

    client.load_table_from_json(

        row,

        TABLE_BATCH,

        job_config=bigquery.LoadJobConfig(

            write_disposition="WRITE_APPEND",

        ),

    ).result()

    return batch


def update_batch(
    batch: DigestBatch,
) -> DigestBatch:
    """
    Update an existing DigestBatch.
    """

    update_bq(

        table=TABLE_BATCH,

        where={

            "ID": batch.id,

        },

        fields={

            "STATUS": batch.status,

            "ITEMS_COUNT": batch.items_count,

            "GENERATED_COUNT": batch.generated_count,

            "SENT_COUNT": batch.sent_count,

            "FAILED_COUNT": batch.failed_count,

            "COMPLETED_AT": batch.completed_at,

        },

    )

    return batch


def fetch_batch(
    batch_id: str,
) -> DigestBatch | None:
    """
    Return a DigestBatch by id.
    """

    sql = f"""
        SELECT
            ID,
            FREQUENCY,
            AUDIENCE,
            PERIOD_START,
            PERIOD_END,
            STATUS,
            ITEMS_COUNT,
            GENERATED_COUNT,
            SENT_COUNT,
            FAILED_COUNT,
            CREATED_AT,
            COMPLETED_AT
        FROM `{TABLE_BATCH}`
        WHERE ID = @id
        LIMIT 1
    """

    rows = query_bq(
        sql,
        {
            "id": batch_id,
        },
    )

    if not rows:
        return None

    return _map_batch(
        rows[0]
    )


def fetch_batches() -> list[DigestBatch]:
    """
    Return the latest DigestBatches.
    """

    sql = f"""
        SELECT
            ID,
            FREQUENCY,
            AUDIENCE,
            PERIOD_START,
            PERIOD_END,
            STATUS,
            ITEMS_COUNT,
            GENERATED_COUNT,
            SENT_COUNT,
            FAILED_COUNT,
            CREATED_AT,
            COMPLETED_AT
        FROM `{TABLE_BATCH}`
        ORDER BY CREATED_AT DESC
    """

    rows = query_bq(sql)

    return [

        _map_batch(row)

        for row in rows

    ]


# ============================================================
# BATCH ITEMS
# ============================================================

def insert_batch_item(
    item: DigestBatchItem,
) -> DigestBatchItem:
    """
    Persist a new DigestBatchItem.
    """

    client = get_bigquery_client()

    row = [{

        "ID": item.id,

        "BATCH_ID": item.batch_id,

        "USER_ID": item.user_id,

        "REVIEW_ID": item.review_id,

        "STATUS": item.status,

        "SELECTED_CONTENTS": item.selected_contents,

        "GENERATED_AT": item.generated_at,

        "SENT_AT": item.sent_at,

        "ERROR": item.error,

    }]

    client.load_table_from_json(

        row,

        TABLE_ITEM,

        job_config=bigquery.LoadJobConfig(

            write_disposition="WRITE_APPEND",

        ),

    ).result()

    return item

def update_batch_item(
    item: DigestBatchItem,
) -> DigestBatchItem:
    """
    Update a DigestBatchItem.
    """

    update_bq(

        table=TABLE_ITEM,

        where={

            "ID": item.id,

        },

        fields={

            "REVIEW_ID": item.review_id,

            "STATUS": item.status,

            "SELECTED_CONTENTS": item.selected_contents,

            "GENERATED_AT": item.generated_at,

            "SENT_AT": item.sent_at,

            "ERROR": item.error,

        },

    )

    return item


def fetch_batch_item(
    item_id: str,
) -> DigestBatchItem | None:
    """
    Return a DigestBatchItem by id.
    """

    sql = f"""
        SELECT
            ID,
            BATCH_ID,
            USER_ID,
            REVIEW_ID,
            STATUS,
            SELECTED_CONTENTS,
            GENERATED_AT,
            SENT_AT,
            ERROR
        FROM `{TABLE_ITEM}`
        WHERE ID = @id
        LIMIT 1
    """

    rows = query_bq(

        sql,

        {

            "id": item_id,

        },

    )

    if not rows:
        return None

    return _map_batch_item(

        rows[0]

    )


def fetch_batch_items(
    batch_id: str,
) -> list[DigestBatchItem]:
    """
    Return every item belonging to a batch.
    """

    sql = f"""
        SELECT
            ID,
            BATCH_ID,
            USER_ID,
            REVIEW_ID,
            STATUS,
            SELECTED_CONTENTS,
            GENERATED_AT,
            SENT_AT,
            ERROR
        FROM `{TABLE_ITEM}`
        WHERE BATCH_ID = @batch_id
        ORDER BY USER_ID
    """

    rows = query_bq(
        sql,
        {
            "batch_id": batch_id,
        },
    )

    return [

        _map_batch_item(row)

        for row in rows

    ]

