# backend/core/digest/send_service.py

from core.digest.models import (
    DigestDocument,
    DeliveryResult,
)


# ============================================================
# SEND DIGEST
# ============================================================

def send_digest(
    document: DigestDocument,
    recipient: str,
) -> DeliveryResult:
    """
    Send a digest to a recipient.

    Pipeline
    --------
    1. Render the DigestDocument into HTML.
    2. Send the email through the configured provider.
    3. Return the delivery result.

    TODO
    ----
    - Render DigestDocument into HTML
    - Integrate the email provider
    """

    raise NotImplementedError
