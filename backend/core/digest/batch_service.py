# backend/core/digest/batch_service.py

from core.digest.models import (
    DigestBatch,
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
    DigestBatchItems.
    """

    raise NotImplementedError


# ============================================================
# GENERATE
# ============================================================

def generate_batch(
    batch: DigestBatch,
) -> DigestBatch:
    """
    Generate every selected digest belonging
    to the batch.
    """

    raise NotImplementedError


# ============================================================
# SEND
# ============================================================

def send_batch(
    batch: DigestBatch,
) -> DigestBatch:
    """
    Deliver every generated digest of the batch.
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

    raise NotImplementedError


# ============================================================
# LIST
# ============================================================

def list_batches() -> list[DigestBatch]:
    """
    Return the latest DigestBatch history.
    """

    raise NotImplementedError

def regenerate_batch_item(
    item_id: str,
):
    """
    Regenerate a single digest.
    """
