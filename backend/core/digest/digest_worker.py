# backend/core/digest/digest_worker.py

import traceback

from core.digest.repository import (
    claim_next_pending_digest,
    fetch_campaign,
    fetch_digests,
    update_campaign,
    update_digest,
)

from core.digest.digest_service import (
    generate_digest,
)

# ============================================================
# PROCESS ONE DIGEST
# ============================================================

def process_next_digest() -> bool:
    """
    Process the next pending digest.

    Returns
    -------
    bool
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

        print(
            f"[FAILED] Campaign not found for digest {digest.id}"
        )

        digest.status = "failed"

        digest.error = "Campaign not found."

        update_digest(
            digest,
        )

        return True

    # ========================================================
    # START CAMPAIGN
    # ========================================================

    if campaign.status == "queued":

        campaign.status = "processing"

        update_campaign(
            campaign,
        )

    # ========================================================
    # GENERATE
    # ========================================================

    try:

        print(
            f"[GENERATING] {digest.user_id}"
        )

        generate_digest(

            digest=digest,

            campaign=campaign,

        )

        digest.status = "generated"

        update_digest(
            digest,
        )

        print(
            f"[OK] {digest.user_id}"
        )

    except Exception as exc:

        traceback.print_exc()

        digest.status = "failed"

        digest.error = str(exc)

        update_digest(
            digest,
        )

        print(
            f"[FAILED] {digest.user_id}"
        )

    # ========================================================
    # UPDATE CAMPAIGN
    # ========================================================

    digests = fetch_digests(
        campaign.id,
    )

    generated = sum(
        d.status == "generated"
        for d in digests
    )

    failed = sum(
        d.status == "failed"
        for d in digests
    )

    campaign.generated_count = generated

    campaign.failed_count = failed

    if generated + failed == len(digests):

        if generated == 0:

            campaign.status = "failed"

        else:

            campaign.status = "generated"

    update_campaign(
        campaign,
    )

    return True


# ============================================================
# PROCESS ALL PENDING DIGESTS
# ============================================================

def process_pending_digests() -> None:
    """
    Process all pending digests.
    """

    print("====================================")
    print("PROCESSING PENDING DIGESTS")
    print("====================================")

    while process_next_digest():

        pass

    print("====================================")
    print("DIGEST PROCESSING COMPLETED")
    print("====================================")
