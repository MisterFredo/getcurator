# backend/core/digest/campaign_service.py

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from calendar import monthrange

from uuid import uuid4

from core.digest.models import (
    Campaign,
    CampaignDetail,
    CampaignCreateRequest,
    Digest,
    DigestRequest,
)

from core.digest.profile_service import (
    get_digest_profiles,
)

from core.digest.digest_service import (
    generate_digest,
)

from core.digest.repository import (
    insert_campaign,
    update_campaign,
    fetch_campaign,
    fetch_campaigns,
    insert_digest,
    update_digest,
    fetch_digests,
)

from core.expertise.constants import (
    OUTPUT_SUMMARY,
    OUTPUT_IMPLICATIONS,
)


# ============================================================
# CREATE
# ============================================================

def create_campaign(
    request: CampaignCreateRequest,
) -> Campaign:

    now = datetime.now(
        timezone.utc,
    )

    # ========================================================
    # PERIOD
    # ========================================================

    if request.frequency == "weekly":

        # Previous complete week (Monday → Sunday)

        current_monday = (
            now
            - timedelta(days=now.weekday())
        ).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        period_end = (
            current_monday
            - timedelta(microseconds=1)
        )

        period_start = (
            current_monday
            - timedelta(days=7)
        )

    else:

        # Previous complete month

        first_day_current_month = now.replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        period_end = (
            first_day_current_month
            - timedelta(microseconds=1)
        )

        period_start = period_end.replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

    # ========================================================
    # CAMPAIGN
    # ========================================================

    campaign = Campaign(

        id=str(uuid4()),

        frequency=request.frequency,

        audience=request.audience,

        period_start=period_start,

        period_end=period_end,

        status="created",

        created_at=now,

    )

    campaign = insert_campaign(
        campaign,
    )

    # ========================================================
    # RECIPIENTS
    # ========================================================

    recipients = get_digest_recipients(
        audience=request.audience,
    )

    campaign.digests_count = len(
        recipients,
    )

    for recipient in recipients:

        digest = Digest(

            campaign_id=campaign.id,

            user_id=recipient.user_id,

        )

        insert_digest(
            digest,
        )

    return update_campaign(
        campaign,
    )


# ============================================================
# GENERATE
# ============================================================

def generate_campaign(
    campaign_id: str,
) -> Campaign:

    campaign = fetch_campaign(
        campaign_id,
    )

    if campaign is None:

        raise ValueError(
            campaign_id,
        )

    campaign.status = "generating"

    update_campaign(
        campaign,
    )

    generated = 0

    failed = 0

    digests = fetch_digests(
        campaign.id,
    )

    for digest in digests:

        try:

            request = DigestRequest(

                user_id=digest.user_id,

                period_start=campaign.period_start,

                period_end=campaign.period_end,

                capabilities=[

                    OUTPUT_SUMMARY,

                    OUTPUT_IMPLICATIONS,

                ],

            )

            generate_digest(

                digest,

                request,

            )

            generated += 1

        except Exception as exc:

            digest.status = "failed"

            digest.error = str(exc)

            update_digest(
                digest,
            )

            failed += 1

    campaign.generated_count = generated

    campaign.failed_count = failed

    campaign.status = "generated"

    return update_campaign(
        campaign,
    )


# ============================================================
# SEND
# ============================================================

def send_campaign(
    campaign_id: str,
) -> Campaign:

    campaign = fetch_campaign(
        campaign_id,
    )

    if campaign is None:

        raise ValueError(
            campaign_id,
        )

    campaign.status = "sending"

    update_campaign(
        campaign,
    )

    sent = 0

    for digest in fetch_digests(
        campaign.id,
    ):

        if digest.status != "generated":

            continue

        #
        # TODO
        # Email service
        #

        digest.status = "sent"

        digest.sent_at = datetime.now(
            timezone.utc,
        )

        update_digest(
            digest,
        )

        sent += 1

    campaign.sent_count = sent

    campaign.status = "completed"

    campaign.completed_at = datetime.now(
        timezone.utc,
    )

    return update_campaign(
        campaign,
    )


# ============================================================
# GET
# ============================================================

def get_campaign(
    campaign_id: str,
) -> CampaignDetail:

    campaign = fetch_campaign(
        campaign_id,
    )

    if campaign is None:

        raise ValueError(
            campaign_id,
        )

    return CampaignDetail(

        campaign=campaign,

        digests=fetch_digests(
            campaign.id,
        ),

    )


# ============================================================
# LIST
# ============================================================

def list_campaigns(
) -> list[Campaign]:

    return fetch_campaigns()
