# backend/core/digest/send_service.py

from core.digest.models import (
    DigestDocument,
)


# ============================================================
# SEND DIGEST
# ============================================================

def send_digest(
    document: DigestDocument,
    recipient: str,
) -> None:

    """
    Send a digest to a recipient.

    TODO
    ----
    - Render DigestDocument into HTML
    - Send email through the selected provider
    """
    raise NotImplementedError
