# backend/core/digest/pipeline.py

from core.digest.models import (
    DigestRequest,
    DeliveryResult,
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
) -> DeliveryResult:
    """
    Execute the complete digest pipeline.

    Pipeline
    --------
    1. Generate the digest review.
    2. Render the editorial document.
    3. Send the digest.
    4. Return the delivery result.
    """

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

    return send_digest(
        document=document,
        recipient=recipient,
    )
