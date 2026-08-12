# backend/api/digest/routes.py

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
)

from core.digest.models import (
    CampaignCreateRequest,
)

from core.digest.campaign_service import (
    create_campaign,
    list_campaigns,
    get_campaign,
    generate_campaign,
    send_campaign,
)

from core.digest.digest_service import (
    get_digest,
    generate_digest,
    send_digest,
    list_digests_for_profile,
)

from core.digest.html_service import (
    render_digest_html,
)

from core.user.user_expert_service import (
    get_user_experts,
)

from utils.auth import (
    get_user_id_from_request,
)


router = APIRouter()


# ============================================================
# CAMPAIGNS
# ============================================================

@router.post("/campaigns")
def create_campaign_route(
    request: CampaignCreateRequest,
):

    return {
        "status": "ok",
        "campaign": create_campaign(
            request,
        ),
    }


@router.get("/campaigns")
def list_campaigns_route():

    return {
        "status": "ok",
        "campaigns": list_campaigns(),
    }


@router.get("/campaigns/{campaign_id}")
def get_campaign_route(
    campaign_id: str,
):

    return {
        "status": "ok",
        "campaign": get_campaign(
            campaign_id,
        ),
    }


# ============================================================
# CAMPAIGN ACTIONS
# ============================================================

@router.post("/campaigns/{campaign_id}/generate")
def generate_campaign_route(
    campaign_id: str,
):

    return {
        "status": "ok",
        "campaign": generate_campaign(
            campaign_id,
        ),
    }


@router.post("/campaigns/{campaign_id}/send")
def send_campaign_route(
    campaign_id: str,
):

    return {
        "status": "ok",
        "campaign": send_campaign(
            campaign_id,
        ),
    }

# ============================================================
# PUBLIC DIGESTS — CURRENT USER
# ============================================================

@router.get("/me")
def list_my_digests_route(
    request: Request,
):

    user_id = get_user_id_from_request(
        request,
    )

    if not user_id:

        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    return {
        "status": "ok",
        "profile_id": user_id,
        "digests": list_digests_for_profile(
            user_id,
        ),
    }


# ============================================================
# PUBLIC DIGESTS — PROFILE / EXPERT
# ============================================================

@router.get(
    "/profiles/{profile_id}",
)
def list_profile_digests_route(
    profile_id: str,
    request: Request,
):

    user_id = get_user_id_from_request(
        request,
    )

    if not user_id:

        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    # ========================================================
    # OWN PROFILE
    # ========================================================

    if profile_id == user_id:

        return {
            "status": "ok",
            "profile_id": profile_id,
            "digests":
                list_digests_for_profile(
                    profile_id,
                ),
        }

    # ========================================================
    # ACCESSIBLE EXPERTS
    # ========================================================

    experts = get_user_experts(
        user_id,
    )

    allowed = any(

        expert.get("ID_USER")
            == profile_id

        and expert.get(
            "IS_SELECTED"
        )

        for expert in experts

    )

    if not allowed:

        raise HTTPException(
            status_code=403,
            detail="Profile not available",
        )

    return {
        "status": "ok",
        "profile_id": profile_id,
        "digests":
            list_digests_for_profile(
                profile_id,
            ),
    }

# ============================================================
# GET DIGEST
# ============================================================

@router.get(
    "/digests/{digest_id}",
)
def get_digest_route(
    digest_id: str,
):

    return {
        "status": "ok",
        "digest": get_digest(
            digest_id,
        ),
    }


# ============================================================
# GENERATE DIGEST
# ============================================================

@router.post(
    "/digests/{digest_id}/generate",
)
def generate_digest_route(
    digest_id: str,
):

    return {
        "status": "ok",
        "digest": generate_digest(
            digest_id,
        ),
    }


# ============================================================
# SEND DIGEST
# ============================================================

@router.post(
    "/digests/{digest_id}/send",
)
def send_digest_route(
    digest_id: str,
):

    return {
        "status": "ok",
        "digest": send_digest(
            digest_id,
        ),
    }

# ============================================================
# PREVIEW
# ============================================================

@router.get(
    "/digests/{digest_id}/preview",
)
def preview_digest_route(
    digest_id: str,
):
    """
    Render the HTML preview of a Digest.
    """

    digest = get_digest(
        digest_id,
    )

    if digest.document is None:

        raise HTTPException(
            status_code=400,
            detail="Digest has not been generated.",
        )

    html = render_digest_html(
        digest.document,
    )

    return {
        "status": "ok",
        "html": html,
    }
