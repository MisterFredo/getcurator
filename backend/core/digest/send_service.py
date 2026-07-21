# backend/core/digest/send_service.py

from core.digest.models import (
    DigestDocument,
)

from core.delivery.models import (
    DeliveryResult,
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
# HTML
# ============================================================

def render_digest_html(
    document: DigestDocument,
) -> str:
    """
    Convert a DigestDocument into
    an HTML email.

    TODO
    ----
    Build the final Curator email template.
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
    Send an HTML email using the
    configured email provider.

    TODO
    ----
    Integrate Resend.
    """

    raise NotImplementedError
