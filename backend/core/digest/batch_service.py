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
    Create a new DigestBatch.
    """

    raise NotImplementedError


# ============================================================
# PREPARE
# ============================================================

def prepare_batch(
    batch_id: str,
):
    """
    Resolve the list of profiles and create
    DigestBatchItems.
    """

    raise NotImplementedError


# ============================================================
# GENERATE
# ============================================================

def generate_batch(
    batch_id: str,
):
    """
    Generate all digests for the selected
    DigestBatchItems.
    """

    raise NotImplementedError


# ============================================================
# SEND
# ============================================================

def send_batch(
    batch_id: str,
):
    """
    Send every generated digest belonging
    to the batch.
    """

    raise NotImplementedError


# ============================================================
# GET
# ============================================================

def get_batch(
    batch_id: str,
) -> DigestBatch:
    """
    Return a DigestBatch with its items.
    """

    raise NotImplementedError


# ============================================================
# LIST
# ============================================================

def list_batches():
    """
    Return the latest DigestBatch history.
    """

    raise NotImplementedError
