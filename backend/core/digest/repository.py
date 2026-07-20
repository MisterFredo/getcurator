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

    raise NotImplementedError


def update_batch(
    batch: DigestBatch,
) -> DigestBatch:
    """
    Update an existing DigestBatch.
    """

    raise NotImplementedError


def fetch_batch(
    batch_id: str,
) -> DigestBatch | None:
    """
    Return a DigestBatch by id.
    """

    raise NotImplementedError


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

    raise NotImplementedError


def update_batch_item(
    item: DigestBatchItem,
) -> DigestBatchItem:
    """
    Update a DigestBatchItem.
    """

    raise NotImplementedError


def fetch_batch_item(
    item_id: str,
) -> DigestBatchItem | None:
    """
    Return a DigestBatchItem by id.
    """

    raise NotImplementedError


def fetch_batch_items(
    batch_id: str,
) -> list[DigestBatchItem]:
    """
    Return every item belonging to a batch.
    """

    raise NotImplementedError


def update_batch_item_status(
    item_id: str,
    status: str,
    error: str | None = None,
    generated_at: datetime | None = None,
    sent_at: datetime | None = None,
) -> None:
    """
    Update the execution status of a DigestBatchItem.
    Optionally update generated_at, sent_at and error.
    """

    raise NotImplementedError
