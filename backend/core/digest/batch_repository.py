# backend/core/digest/batch_repository.py

from datetime import datetime

from core.digest.models import (
    DigestBatch,
    DigestBatchItem,
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
    Return the latest DigestBatch history.
    """
    raise NotImplementedError


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
    review_id: str | None = None,
    generated_at: datetime | None = None,
    sent_at: datetime | None = None,
    error: str | None = None,
) -> None:
    """
    Update the processing status of a DigestBatchItem.
    """
    raise NotImplementedError
