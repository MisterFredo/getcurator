from datetime import datetime

from google.cloud import bigquery

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
    update_bq,
    get_bigquery_client,
)

from core.digest.models import (
    DigestBatch,
    DigestBatchItem,
)

TABLE_BATCH = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_DIGEST_BATCH"
)

TABLE_BATCH_ITEM = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_DIGEST_BATCH_ITEM"
)

# ============================================================
# INSERT BATCH
# ============================================================

def insert_batch(
    batch: DigestBatch,
) -> DigestBatch:
    """
    Persist a new DigestBatch.
    """

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

    client = get_bigquery_client()

    client.load_table_from_json(

        row,

        TABLE_BATCH,

        job_config=bigquery.LoadJobConfig(

            write_disposition="WRITE_APPEND",

        ),

    ).result()

    return batch

# ============================================================
# UPDATE BATCH
# ============================================================

def update_batch(
    batch: DigestBatch,
) -> DigestBatch:
    """
    Update an existing DigestBatch.
    """

    update_bq(

        table=TABLE_BATCH,

        fields={

            "FREQUENCY": batch.frequency,
            "AUDIENCE": batch.audience,

            "PERIOD_START": batch.period_start,
            "PERIOD_END": batch.period_end,

            "STATUS": batch.status,

            "ITEMS_COUNT": batch.items_count,
            "GENERATED_COUNT": batch.generated_count,
            "SENT_COUNT": batch.sent_count,
            "FAILED_COUNT": batch.failed_count,

            "CREATED_AT": batch.created_at,

            "COMPLETED_AT": batch.completed_at,

        },

        where={

            "ID": batch.id,

        },

    )

    return batch

# ============================================================
# FETCH BATCH
# ============================================================

def fetch_batch(
    batch_id: str,
) -> DigestBatch | None:
    """
    Return a DigestBatch by id.
    """

    rows = query_bq(

        f"""
        SELECT *
        FROM `{TABLE_BATCH}`
        WHERE ID = @id
        LIMIT 1
        """,

        {

            "id": batch_id,

        },

    )

    if not rows:

        return None

    row = rows[0]

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

        completed_at=row.get(
            "COMPLETED_AT",
        ),

    )

# ============================================================
# FETCH BATCHES
# ============================================================

def fetch_batches() -> list[DigestBatch]:
    """
    Return the latest DigestBatch history.
    """

    rows = query_bq(

        f"""
        SELECT *
        FROM `{TABLE_BATCH}`
        ORDER BY CREATED_AT DESC
        """,

    )

    batches: list[DigestBatch] = []

    for row in rows:

        batches.append(

            DigestBatch(

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

                completed_at=row.get(
                    "COMPLETED_AT",
                ),

            )

        )

    return batches

# ============================================================
# INSERT BATCH ITEM
# ============================================================

def insert_batch_item(
    item: DigestBatchItem,
) -> DigestBatchItem:
    """
    Persist a new DigestBatchItem.
    """

    row = [{

        "ID": item.id,

        "BATCH_ID": item.batch_id,

        "USER_ID": item.user_id,

        "REVIEW_ID": item.review_id,

        "STATUS": item.status,

        "SELECTED_CONTENTS": item.selected_contents,

        "GENERATED_AT": (
            item.generated_at.isoformat()
            if item.generated_at
            else None
        ),

        "SENT_AT": (
            item.sent_at.isoformat()
            if item.sent_at
            else None
        ),

        "ERROR": item.error,

    }]

    client = get_bigquery_client()

    client.load_table_from_json(

        row,

        TABLE_BATCH_ITEM,

        job_config=bigquery.LoadJobConfig(

            write_disposition="WRITE_APPEND",

        ),

    ).result()

    return item

# ============================================================
# UPDATE BATCH ITEM
# ============================================================

def update_batch_item(
    item: DigestBatchItem,
) -> DigestBatchItem:
    """
    Update a DigestBatchItem.
    """

    update_bq(

        table=TABLE_BATCH_ITEM,

        fields={

            "BATCH_ID": item.batch_id,

            "USER_ID": item.user_id,

            "REVIEW_ID": item.review_id,

            "STATUS": item.status,

            "SELECTED_CONTENTS": item.selected_contents,

            "GENERATED_AT": item.generated_at,

            "SENT_AT": item.sent_at,

            "ERROR": item.error,

        },

        where={

            "ID": item.id,

        },

    )

    return item

# ============================================================
# FETCH BATCH ITEM
# ============================================================

def fetch_batch_item(
    item_id: str,
) -> DigestBatchItem | None:
    """
    Return a DigestBatchItem by id.
    """

    rows = query_bq(

        f"""
        SELECT *
        FROM `{TABLE_BATCH_ITEM}`
        WHERE ID = @id
        LIMIT 1
        """,

        {
            "id": item_id,
        },

    )

    if not rows:
        return None

    row = rows[0]

    return DigestBatchItem(

        id=row["ID"],

        batch_id=row["BATCH_ID"],

        user_id=row["USER_ID"],

        review_id=row.get(
            "REVIEW_ID",
        ),

        status=row["STATUS"],

        selected_contents=row[
            "SELECTED_CONTENTS"
        ],

        generated_at=row.get(
            "GENERATED_AT",
        ),

        sent_at=row.get(
            "SENT_AT",
        ),

        error=row.get(
            "ERROR",
        ),

    )

# ============================================================
# FETCH BATCH ITEMS
# ============================================================

def fetch_batch_items(
    batch_id: str,
) -> list[DigestBatchItem]:
    """
    Return every DigestBatchItem
    belonging to a batch.
    """

    rows = query_bq(

        f"""
        SELECT *
        FROM `{TABLE_BATCH_ITEM}`
        WHERE BATCH_ID = @batch_id
        ORDER BY USER_ID
        """,

        {
            "batch_id": batch_id,
        },

    )

    items: list[DigestBatchItem] = []

    for row in rows:

        items.append(

            DigestBatchItem(

                id=row["ID"],

                batch_id=row["BATCH_ID"],

                user_id=row["USER_ID"],

                review_id=row.get(
                    "REVIEW_ID",
                ),

                status=row["STATUS"],

                selected_contents=row[
                    "SELECTED_CONTENTS"
                ],

                generated_at=row.get(
                    "GENERATED_AT",
                ),

                sent_at=row.get(
                    "SENT_AT",
                ),

                error=row.get(
                    "ERROR",
                ),

            )

        )

    return items

# ============================================================
# UPDATE BATCH ITEM STATUS
# ============================================================

def update_batch_item_status(
    item_id: str,
    status: str,
    review_id: str | None = None,
    generated_at: datetime | None = None,
    sent_at: datetime | None = None,
    error: str | None = None,
) -> None:
    """
    Update the processing status
    of a DigestBatchItem.
    """

    fields = {

        "STATUS": status,

    }

    if review_id is not None:

        fields["REVIEW_ID"] = review_id

    if generated_at is not None:

        fields["GENERATED_AT"] = generated_at

    if sent_at is not None:

        fields["SENT_AT"] = sent_at

    if error is not None:

        fields["ERROR"] = error

    update_bq(

        table=TABLE_BATCH_ITEM,

        fields=fields,

        where={

            "ID": item_id,

        },

    )
