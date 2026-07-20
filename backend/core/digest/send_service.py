# backend/core/digest/send_service.py

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from core.digest.models import (
    DigestDocument,
)

from core.delivery.models import (
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
    Deliver a DigestDocument to a recipient.
    """

    # ========================================================
    # RENDER HTML
    # ========================================================

    html = render_digest_html(
        document,
    )

    # ========================================================
    # SEND EMAIL
    # ========================================================

    return send_email(

        recipient=recipient,

        subject=document.title,

        html=html,

    )


# ============================================================
# RENDER
# ============================================================

def render_digest_html(
    document: DigestDocument,
) -> str:
    """
    Render a DigestDocument into HTML.

    TODO
    ----
    Convert the DigestDocument into the
    final HTML email template.
    """

    raise NotImplementedError


# ============================================================
# EMAIL
# ============================================================

def send_email(
    recipient: str,
    subject: str,
    html: str,
) -> DeliveryResult:
    """
    Send an HTML email through the configured
    email provider.

    TODO
    ----
    Integrate Resend (or another provider).
    """

    raise NotImplementedError
