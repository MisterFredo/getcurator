from datetime import (
    datetime,
    timedelta,
    timezone,
)

from uuid import uuid4
import traceback

from core.digest.models import (
    Campaign,
    CampaignDetail,
    CampaignDigest,
    CampaignCreateRequest,
    Digest,
)

from core.digest.profile_service import (
    get_digest_recipients,
)

from core.digest.digest_service import (
    generate_digest,
)

from core.digest.repository import (
    insert_campaign,
    update_campaign,
    fetch_campaign,
    fetch_campaigns,
    fetch_campaign_for_period,
    insert_digest,
    update_digest,
    fetch_digest_for_period,
    fetch_digests,
)

from core.user.user_service import (
    list_users,
)


# ============================================================
# CONFIGURATION
# ============================================================

DIGEST_FREQUENCY = "weekly"


# ============================================================
# CREATE FOR PERIOD
# ============================================================

def create_campaign_for_period(
    audience: str,
    period_start: datetime,
    period_end: datetime,
    user_ids: list[str] | None = None,
) -> Campaign:
    """
    Create a weekly Digest Campaign for one exact period.

    When user_ids is None, recipients are resolved
    from their profile type.

    When user_ids is provided, only these profiles
    are considered. This mode is used by bootstrap.
    """

    # ========================================================
    # STANDARD CAMPAIGN IDEMPOTENCE
    # ========================================================

    if user_ids is None:

        existing_campaign = (
            fetch_campaign_for_period(

                frequency=DIGEST_FREQUENCY,

                audience=audience,

                period_start=period_start,

                period_end=period_end,

            )
        )

        if existing_campaign is not None:

            return existing_campaign

    # ========================================================
    # RECIPIENTS
    # ========================================================

    if user_ids is None:

        recipients = get_digest_recipients(
            audience=audience,
        )

        recipient_ids = [

            recipient.user_id

            for recipient in recipients

        ]

    else:

        # Preserve order while removing duplicates.

        recipient_ids = list(
            dict.fromkeys(
                user_ids,
            )
        )

    # ========================================================
    # REMOVE EXISTING DIGESTS
    # ========================================================

    missing_user_ids = []

    first_existing_digest = None

    for user_id in recipient_ids:

        existing_digest = fetch_digest_for_period(

            user_id=user_id,

            frequency=DIGEST_FREQUENCY,

            period_start=period_start,

            period_end=period_end,

        )

        if existing_digest is not None:

            if first_existing_digest is None:

                first_existing_digest = (
                    existing_digest
                )

            continue

        missing_user_ids.append(
            user_id,
        )

    # ========================================================
    # NOTHING TO CREATE
    # ========================================================

    if not missing_user_ids:

        if first_existing_digest is not None:

            existing_campaign = fetch_campaign(
                first_existing_digest.campaign_id,
            )

            if existing_campaign is not None:

                return existing_campaign

        # Preserve the current behavior for an audience
        # containing no eligible recipient: an empty Campaign
        # is still created for traceability.

        if recipient_ids:

            raise ValueError(
                "Unable to resolve existing Digest Campaign."
            )

    # ========================================================
    # CAMPAIGN
    # ========================================================

    now = datetime.now(
        timezone.utc,
    )

    campaign = Campaign(

        id=str(uuid4()),

        frequency=DIGEST_FREQUENCY,

        audience=audience,

        period_start=period_start,

        period_end=period_end,

        status="created",

        digests_count=len(
            missing_user_ids,
        ),

        created_at=now,

    )

    insert_campaign(
        campaign,
    )

    # ========================================================
    # DIGESTS
    # ========================================================

    for user_id in missing_user_ids:

        digest = Digest(

            campaign_id=campaign.id,

            user_id=user_id,

            status="created",

            total_contents=0,

            analyzed_contents=0,

        )

        insert_digest(
            digest,
        )

    return campaign


# ============================================================
# CREATE
# ============================================================

def create_campaign(
    request: CampaignCreateRequest,
) -> Campaign:
    """
    Create the weekly Digest Campaign for the
    previous complete week.
    """

    if request.frequency != DIGEST_FREQUENCY:

        raise ValueError(
            "A Digest Campaign must be weekly."
        )

    now = datetime.now(
        timezone.utc,
    )

    # Previous complete week: Monday → Sunday.

    current_monday = (

        now

        - timedelta(
            days=now.weekday(),
        )

    ).replace(

        hour=0,
        minute=0,
        second=0,
        microsecond=0,

    )

    period_end = (

        current_monday

        - timedelta(
            microseconds=1,
        )

    )

    period_start = (

        current_monday

        - timedelta(
            days=7,
        )

    )

    return create_campaign_for_period(

        audience=request.audience,

        period_start=period_start,

        period_end=period_end,

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

    # ========================================================
    # START CAMPAIGN
    # ========================================================

    campaign.status = "generating"

    update_campaign(
        campaign,
    )

    generated = 0

    failed = 0

    digests = fetch_digests(
        campaign.id,
    )

    # ========================================================
    # GENERATE DIGESTS
    # ========================================================

    for digest in digests:

        # Existing immutable Digest:
        # count it without regenerating it.

        if digest.status in (
            "generated",
            "sent",
        ):

            generated += 1

            continue

        try:

            generate_digest(
                digest.id,
            )

            generated += 1

        except Exception:

            traceback.print_exc()

            failed += 1

    # ========================================================
    # UPDATE CAMPAIGN
    # ========================================================

    campaign.digests_count = len(
        digests,
    )

    campaign.generated_count = generated

    campaign.failed_count = failed

    if generated == 0:

        campaign.status = "failed"

    else:

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

    # ========================================================
    # USERS
    # ========================================================

    users = {

        user["ID_USER"]:
            user

        for user in list_users()

    }

    # ========================================================
    # DIGESTS
    # ========================================================

    digests = []

    for digest in fetch_digests(
        campaign.id,
    ):

        user = users.get(
            digest.user_id,
        )

        digests.append(

            CampaignDigest(

                **digest.model_dump(),

                user_name=(

                    user.get("DISPLAY_NAME")

                    or user.get("NAME")

                    if user

                    else None

                ),

                user_email=(

                    user.get("EMAIL")

                    if user

                    else None

                ),

            )

        )

    # ========================================================
    # RESPONSE
    # ========================================================

    return CampaignDetail(

        campaign=campaign,

        digests=digests,

    )


# ============================================================
# LIST
# ============================================================

def list_campaigns(
) -> list[Campaign]:

    return fetch_campaigns()
