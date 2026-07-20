# backend/core/digest/batch_service.py

from datetime import (
    datetime,
    timedelta,
    timezone,
)
from uuid import uuid4
from typing import Literal

from core.digest.models import (
    DigestRequest,
    DigestBatch,
    DigestBatchItem,
    DigestReview,
    DigestBatchDetail,
)

from core.digest.profile_service import (
    get_digest_profiles,
)

from core.digest.review_service import (
    generate_review,
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
    frequency: Literal[
        "weekly",
        "monthly",
    ],
    audience: Literal[
        "user",
        "expert",
    ],
) -> DigestBatch:
    """
    Create and persist a new DigestBatch.
    """

    now = datetime.now(
        timezone.utc,
    )

    if frequency == "weekly":

        period_start = (
            now - timedelta(days=7)
        )

    elif frequency == "monthly":

        period_start = (
            now - timedelta(days=30)
        )

    else:

        raise ValueError(
            f"Unknown frequency: {frequency}"
        )

    batch = DigestBatch(

        id=str(uuid4()),

        frequency=frequency,
        audience=audience,

        period_start=period_start,
        period_end=now,

        status="created",

        items_count=0,
        generated_count=0,
        sent_count=0,
        failed_count=0,

        created_at=now,

        completed_at=None,

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

    items = fetch_batch_items(
        batch_id=batch.id,
    )

    batch.status = "generating"

    update_batch(
        batch,
    )

    generated = 0
    failed = 0

    for item in items:

        try:

            regenerate_batch_item(
                item.id,
            )

            generated += 1

        except Exception:

            failed += 1

    batch.generated_count = generated
    batch.failed_count = failed

    batch.status = "generated"

    return update_batch(
        batch,
    )


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

    items = fetch_batch_items(
        batch_id=batch.id,
    )

    batch.status = "sending"

    update_batch(
        batch,
    )

    sent = 0
    failed = batch.failed_count

    for item in items:

        if item.status != "generated":
            continue

        try:

            # ====================================================
            # TODO
            # ====================================================
            # Resolve recipients
            # Render digest document
            # Send email
            # ====================================================

            update_batch_item_status(

                item_id=item.id,

                status="sent",

                sent_at=datetime.now(
                    timezone.utc,
                ),

            )

            sent += 1

        except Exception as exc:

            failed += 1

            update_batch_item_status(

                item_id=item.id,

                status="failed",

                error=str(exc),

            )

    batch.sent_count = sent
    batch.failed_count = failed

    batch.status = "completed"

    batch.completed_at = datetime.now(
        timezone.utc,
    )

    return update_batch(
        batch,
    )
# ============================================================
# ITEM
# ============================================================

def regenerate_batch_item(
    item_id: str,
) -> DigestReview:
    """
    Regenerate a single DigestBatchItem.
    """

    # ========================================================
    # LOAD ITEM
    # ========================================================

    item = fetch_batch_item(
        item_id=item_id,
    )

    if item is None:

        raise ValueError(
            f"Unknown batch item: {item_id}"
        )

    batch = fetch_batch(
        batch_id=item.batch_id,
    )

    if batch is None:

        raise ValueError(
            f"Unknown batch: {item.batch_id}"
        )

    update_batch_item_status(

        item_id=item.id,

        status="generating",

    )

    try:

        # ====================================================
        # BUILD REQUEST
        # ====================================================

        request = DigestRequest(

            user_id=item.user_id,

            period_start=batch.period_start,

            period_end=batch.period_end,

            capabilities=[
                "summary",
                "implications",
            ],

        )

        # ====================================================
        # GENERATE REVIEW
        # ====================================================

        review = generate_digest_review(
            request=request,
        )

        # ====================================================
        # SAVE REVIEW
        # ====================================================

        item.review_id = review.id

        item.generated_at = datetime.now(
            timezone.utc,
        )

        update_batch_item(
            item,
        )

        update_batch_item_status(

            item_id=item.id,

            status="generated",

        )

        return review

    except Exception as exc:

        update_batch_item_status(

            item_id=item.id,

            status="failed",

            error=str(exc),

        )

        raise


def get_batch(
    batch_id: str,
) -> DigestBatchDetail:
    """
    Return a DigestBatch with its items.
    """

    batch = fetch_batch(
        batch_id=batch_id,
    )

    if batch is None:

        raise ValueError(
            f"Unknown batch: {batch_id}"
        )

    items = fetch_batch_items(
        batch_id=batch_id,
    )

    return DigestBatchDetail(

        batch=batch,

        items=items,

    )

def list_batches() -> list[DigestBatch]:
    """
    Return the latest DigestBatch history.
    """

    return fetch_batches()
