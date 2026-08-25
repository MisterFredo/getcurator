from core.digest.bootstrap_service import (
    bootstrap_profile_digests,
)

from core.digest.campaign_service import (
    create_campaign,
    generate_campaign,
)

from core.digest.models import (
    CampaignCreateRequest,
)

from core.user.user_service import (
    list_users,
)


# ============================================================
# BOOTSTRAP ALL PROFILES
# ============================================================

def bootstrap_all_profiles(
) -> dict:
    """
    Ensure that every active USER and EXPERT
    has its three most recent Digests.
    """

    users = list_users()

    eligible_users = [

        user

        for user in users

        if (
            bool(
                user.get("IS_ACTIVE")
            )

            and (
                user.get("PROFILE_TYPE")
                or "USER"
            ).upper()
            in (
                "USER",
                "EXPERT",
            )
        )

    ]

    result = {

        "status":
            "completed",

        "profiles_count":
            len(eligible_users),

        "processed_count":
            0,

        "created_count":
            0,

        "generated_count":
            0,

        "skipped_count":
            0,

        "failed_count":
            0,

        "profiles":
            [],

    }

    for user in eligible_users:

        user_id = user.get(
            "ID_USER"
        )

        if not user_id:

            continue

        try:

            profile_result = (
                bootstrap_profile_digests(
                    user_id=user_id,
                )
            )

            result["processed_count"] += 1

            result["created_count"] += (
                profile_result.get(
                    "created_count",
                    0,
                )
            )

            result["generated_count"] += (
                profile_result.get(
                    "generated_count",
                    0,
                )
            )

            result["skipped_count"] += (
                profile_result.get(
                    "skipped_count",
                    0,
                )
            )

            result["failed_count"] += (
                profile_result.get(
                    "failed_count",
                    0,
                )
            )

            result["profiles"].append({

                "user_id":
                    user_id,

                "name": (
                    user.get("DISPLAY_NAME")
                    or user.get("NAME")
                    or user_id
                ),

                "profile_type":
                    user.get("PROFILE_TYPE"),

                "status":
                    profile_result.get(
                        "status"
                    ),

                "created_count":
                    profile_result.get(
                        "created_count",
                        0,
                    ),

                "generated_count":
                    profile_result.get(
                        "generated_count",
                        0,
                    ),

                "skipped_count":
                    profile_result.get(
                        "skipped_count",
                        0,
                    ),

                "failed_count":
                    profile_result.get(
                        "failed_count",
                        0,
                    ),

            })

        except Exception as exc:

            result["processed_count"] += 1

            result["failed_count"] += 1

            result["profiles"].append({

                "user_id":
                    user_id,

                "name": (
                    user.get("DISPLAY_NAME")
                    or user.get("NAME")
                    or user_id
                ),

                "profile_type":
                    user.get("PROFILE_TYPE"),

                "status":
                    "failed",

                "error":
                    str(exc),

            })

    if result["failed_count"]:

        successful_count = (

            result["generated_count"]

            + result["skipped_count"]

        )

        if successful_count:

            result["status"] = "partial"

        else:

            result["status"] = "failed"

    return result


# ============================================================
# GENERATE ALL DIGESTS
# ============================================================

def generate_all_digests(
) -> dict:
    """
    Create and generate the previous complete
    week's Campaigns for USER and EXPERT profiles.
    """

    result = {

        "status":
            "completed",

        "campaigns_count":
            0,

        "digests_count":
            0,

        "generated_count":
            0,

        "failed_count":
            0,

        "campaigns":
            [],

    }

    for audience in (
        "user",
        "expert",
    ):

        try:

            campaign = create_campaign(

                CampaignCreateRequest(
                    audience=audience,
                )

            )

            campaign = generate_campaign(
                campaign.id,
            )

            result["campaigns_count"] += 1

            result["digests_count"] += (
                campaign.digests_count
            )

            result["generated_count"] += (
                campaign.generated_count
            )

            result["failed_count"] += (
                campaign.failed_count
            )

            result["campaigns"].append({

                "campaign_id":
                    campaign.id,

                "audience":
                    campaign.audience,

                "status":
                    campaign.status,

                "period_start":
                    campaign.period_start.isoformat(),

                "period_end":
                    campaign.period_end.isoformat(),

                "digests_count":
                    campaign.digests_count,

                "generated_count":
                    campaign.generated_count,

                "failed_count":
                    campaign.failed_count,

            })

        except Exception as exc:

            result["failed_count"] += 1

            result["campaigns"].append({

                "audience":
                    audience,

                "status":
                    "failed",

                "error":
                    str(exc),

            })

    if result["failed_count"]:

        if result["generated_count"]:

            result["status"] = "partial"

        else:

            result["status"] = "failed"

    return result
