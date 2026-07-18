# backend/core/digest/pipeline.py

from core.digest.models import (
    DigestRequest,
)

from core.digest.service import (
    generate_digest_review,
)

from core.digest.render_service import (
    render_digest,
)

from core.digest.send_service import (
    send_digest,
)


# ============================================================
# RUN DIGEST
# ============================================================

def run_digest(
    request: DigestRequest,
    recipient: str,
) -> None:

    # ========================================================
    # REVIEW
    # ========================================================

    review = generate_digest_review(
        request,
    )

    # ========================================================
    # DOCUMENT
    # ========================================================

    document = render_digest(
        review,
    )

    # ========================================================
    # SEND
    # ========================================================

    send_digest(
        document=document,
        recipient=recipient,
    )
