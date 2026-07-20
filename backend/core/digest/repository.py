# backend/core/digest/batch_service.py

from datetime import datetime, timezone
from uuid import uuid4

from core.digest.models import (
    DigestBatch,
    DigestBatchItem,
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

    batch = DigestBatch(

        id=str(uuid4()),

        frequency=frequency,
        audience=audience,

        status="created",

        items_count=0,
        generated_count=0,
        sent_count=0,
        failed_count=0,

        created_at=datetime.now(
            timezone.utc,
        ),

    )

    return insert_batch(
        batch,
    )


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

    profiles = get_digest_profiles(

        frequency=batch.frequency,

        audience=batch.audience,

    )

    for profile in profiles:

        item = DigestBatchItem(

            id=str(uuid4()),

            batch_id=batch.id,

            user_id=profile.user_id,

            review_id=None,

            status="pending",

            recipients_count=profile.recipients_count,

            selected_contents=0,

            generated_at=None,

            sent_at=None,

            error=None,

        )

        insert_batch_item(
            item,
        )

    batch.items_count = len(
        profiles,
    )

    batch.status = "prepared"

    return update_batch(
        batch,
    )


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
