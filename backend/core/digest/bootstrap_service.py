from datetime import (
    datetime,
    timedelta,
    timezone,
)

from core.digest.campaign_service import (
    create_campaign_for_period,
)

from core.digest.digest_service import (
    generate_digest,
)

from core.digest.repository import (
    fetch_campaign,
    fetch_digest_for_period,
    fetch_digests,
    update_campaign,
)

from core.user.user_service import (
    get_user,
)


# ============================================================
# CONFIGURATION
# ============================================================

BOOTSTRAP_WEEKS_COUNT = 3


# ============================================================
# BOOTSTRAP
# ============================================================

def bootstrap_profile_digests(
    user_id: str,
) -> dict:
    """
    Ensure that one profile has its three most
    recent complete weekly Digests.

    Existing generated or sent Digests are never
    regenerated.

    Existing created or failed Digests are retried.
    """

    # ========================================================
    # USER
    # ========================================================

    user = get_user(
        user_id,
    )

    if user is None:

        raise ValueError(
            f"Unknown user: {user_id}"
        )

    profile_type = (
        user.get("PROFILE_TYPE")
        or "USER"
    ).upper()

    audience = (

        "expert"

        if profile_type == "EXPERT"

        else "user"

    )

    # ========================================================
    # RESULT
    # ========================================================

    result = {

        "status":
            "completed",

        "user_id":
            user_id,

        "audience":
            audience,

        "created_count":
            0,

        "generated_count":
            0,

        "skipped_count":
            0,

        "failed_count":
            0,

        "digests":
            [],

    }

    # ========================================================
    # PERIODS
    # ========================================================

    periods = _build_weekly_periods(
        count=BOOTSTRAP_WEEKS_COUNT,
    )

    # ========================================================
    # DIGESTS
    # ========================================================

    for period_start, period_end in periods:

        digest = fetch_digest_for_period(

            user_id=user_id,
            period_start=period_start,

            period_end=period_end,

        )

        created = False

        # ====================================================
        # CREATE MISSING DIGEST
        # ====================================================

        if digest is None:

            campaign = create_campaign_for_period(

                audience=audience,

                period_start=period_start,

                period_end=period_end,

                user_ids=[
                    user_id,
                ],

            )

            campaign_digests = fetch_digests(
                campaign.id,
            )

            digest = next(

                (

                    item

                    for item in campaign_digests

                    if item.user_id == user_id

                ),

                None,

            )

            if digest is None:

                result["failed_count"] += 1

                result["digests"].append({

                    "period_start":
                        period_start.isoformat(),

                    "period_end":
                        period_end.isoformat(),

                    "status":
                        "failed",

                    "error":
                        "Digest was not created.",

                })

                continue

            created = True

            result["created_count"] += 1

        # ====================================================
        # IMMUTABLE DIGEST
        # ====================================================

        if digest.status in (
            "generated",
            "sent",
        ):

            result["skipped_count"] += 1

            result["digests"].append({

                "digest_id":
                    digest.id,

                "campaign_id":
                    digest.campaign_id,

                "period_start":
                    period_start.isoformat(),

                "period_end":
                    period_end.isoformat(),

                "status":
                    digest.status,

                "created":
                    created,

            })

            continue

        # ====================================================
        # GENERATE OR RETRY
        # ====================================================

        try:

            generated_digest = generate_digest(
                digest.id,
            )

            result["generated_count"] += 1

            result["digests"].append({

                "digest_id":
                    generated_digest.id,

                "campaign_id":
                    generated_digest.campaign_id,

                "period_start":
                    period_start.isoformat(),

                "period_end":
                    period_end.isoformat(),

                "status":
                    generated_digest.status,

                "created":
                    created,

            })

        except Exception as exc:

            result["failed_count"] += 1

            result["digests"].append({

                "digest_id":
                    digest.id,

                "campaign_id":
                    digest.campaign_id,

                "period_start":
                    period_start.isoformat(),

                "period_end":
                    period_end.isoformat(),

                "status":
                    "failed",

                "created":
                    created,

                "error":
                    str(exc),

            })

        finally:

            _refresh_campaign_generation(
                digest.campaign_id,
            )

    # ========================================================
    # FINAL STATUS
    # ========================================================

    if result["failed_count"]:

        available_count = (

            result["generated_count"]

            + result["skipped_count"]

        )

        if available_count:

            result["status"] = "partial"

        else:

            result["status"] = "failed"

    return result


# ============================================================
# WEEKLY PERIODS
# ============================================================

def _build_weekly_periods(
    count: int,
) -> list[tuple[datetime, datetime]]:
    """
    Return the most recent complete calendar weeks,
    ordered from newest to oldest.

    A complete week runs from Monday at 00:00 UTC
    to Sunday at 23:59:59.999999 UTC.
    """

    now = datetime.now(
        timezone.utc,
    )

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

    cursor = current_monday

    periods = []

    for _ in range(count):

        period_end = (

            cursor

            - timedelta(
                microseconds=1,
            )

        )

        period_start = (

            cursor

            - timedelta(
                days=7,
            )

        )

        periods.append(
            (
                period_start,
                period_end,
            )
        )

        cursor = period_start

    return periods


# ============================================================
# REFRESH CAMPAIGN
# ============================================================

def _refresh_campaign_generation(
    campaign_id: str,
) -> None:
    """
    Synchronize Campaign generation counters after
    one bootstrap Digest generation or retry.
    """

    campaign = fetch_campaign(
        campaign_id,
    )

    if campaign is None:

        return

    digests = fetch_digests(
        campaign_id,
    )

    campaign.digests_count = len(
        digests,
    )

    campaign.generated_count = len([

        digest

        for digest in digests

        if digest.status in (
            "generated",
            "sent",
        )

    ])

    campaign.failed_count = len([

        digest

        for digest in digests

        if digest.status == "failed"

    ])

    # Do not downgrade a Campaign that was already sent.

    if campaign.status not in (
        "sending",
        "completed",
    ):

        if campaign.generated_count == 0:

            campaign.status = (

                "failed"

                if campaign.failed_count

                else "created"

            )

        else:

            campaign.status = "generated"

    update_campaign(
        campaign,
    )
