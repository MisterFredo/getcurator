# backend/core/digest/digest_worker.py

import time
import traceback

from core.digest.repository import (
    claim_next_pending_digest,
    update_digest,
    fetch_campaign,
)

from core.digest.digest_service import (
    generate_digest,
)

# ============================================================
# CONFIG
# ============================================================

POLL_INTERVAL = 5

# ============================================================
# PROCESS
# ============================================================

def process_next_digest() -> bool:
    """
    Process the next pending digest.

    Returns
    -------
    True if a digest was processed.
    False if no pending digest was found.
    """

    digest = claim_next_pending_digest()

    if digest is None:
        return False

    campaign = fetch_campaign(
        digest.campaign_id,
    )

    if campaign is None:

        digest.status = "failed"

        digest.error = (
            "Campaign not found."
        )

        update_digest(
            digest,
        )

        return True

    try:

        generate_digest(

            digest=digest,

            campaign=campaign,

        )

        digest.status = "generated"

        update_digest(
            digest,
        )

    except Exception as exc:

        traceback.print_exc()

        digest.status = "failed"

        digest.error = str(exc)

        update_digest(
            digest,
        )

    return True


# ============================================================
# LOOP
# ============================================================

def run() -> None:
    """
    Background worker.
    """

    print("====================================")
    print("Digest Worker started")
    print("====================================")

    while True:

        processed = process_next_digest()

        if not processed:

            time.sleep(
                POLL_INTERVAL,
            )


# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":

    run()
