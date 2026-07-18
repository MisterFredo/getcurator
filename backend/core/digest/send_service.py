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

    html = render_email(
        document,
    )

    send_email(
        to=recipient,
        subject=document.title,
        html=html,
    )
