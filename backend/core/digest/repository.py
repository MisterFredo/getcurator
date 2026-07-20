# backend/core/digest/batch_service.py

from core.digest.models import (
    DigestBatch,
)

from core.digest.profile_service import (
    get_digest_profiles,
)

from core.digest.repository import (
    insert_batch,
    update_batch,
    fetch_batch,
    fetch_batches,
    insert_batch_item,
    update_batch_item,
    fetch_batch_item,
    fetch_batch_items,
    update_batch_item_status,
)


# ============================================================
# CREATE
# ============================================================

def create_batch(
    frequency: str,
    audience: str,
) -> DigestBatch:
    """
    Create and persist a new DigestBatch.
    """

    raise NotImplementedError


# ============================================================
# PREPARE
# ============================================================

def prepare_batch(
    batch: DigestBatch,
) -> DigestBatch:
    """
    Resolve eligible profiles and create
    DigestBatchItems for the batch.
    """

    raise NotImplementedError


# ============================================================
# GENERATE
# ============================================================

def generate_batch(
    batch: DigestBatch,
) -> DigestBatch:
    """
    Generate every DigestReview
    belonging to the batch.
    """

    raise NotImplementedError


# ============================================================
# SEND
# ============================================================

def send_batch(
    batch: DigestBatch,
) -> DigestBatch:
    """
    Deliver every generated digest
    belonging to the batch.
    """

    raise NotImplementedError


# ============================================================
# ITEM
# ============================================================

def regenerate_batch_item(
    item_id: str,
):
    """
    Regenerate a single DigestBatchItem.
    """

    raise NotImplementedError


# ============================================================
# GET
# ============================================================

def get_batch(
    batch_id: str,
) -> DigestBatch:
    """
    Return a DigestBatch.
    """

    return fetch_batch(
        batch_id=batch_id,
    )


# ============================================================
# LIST
# ============================================================

def list_batches() -> list[DigestBatch]:
    """
    Return the latest DigestBatch history.
    """

    return fetch_batches()
