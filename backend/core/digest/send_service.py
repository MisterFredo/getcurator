# backend/core/digest/send_service.py

from core.digest.models import (
    DigestDocument,
)

from core.delivery.models import (
    DeliveryResult,
)

from core.digest.html_service import (
    render_digest_html,
)


# ============================================================
# SEND
# ============================================================

def send_digest(
    recipient: str,
    document: DigestDocument,
) -> DeliveryResult:
    """
    Deliver a DigestDocument by email.
    """

    html = render_digest_html(
        document,
    )

    return send_email(

        recipient=recipient,

        subject=document.title,

        html=html,

    )


# ============================================================
# EMAIL
# ============================================================

def send_email(
    recipient: str,
    subject: str,
    html: str,
) -> DeliveryResult:
    """
    Send an HTML email using the
    configured email provider.

    TODO
    ----
    Integrate Resend.
    """

    raise NotImplementedError
