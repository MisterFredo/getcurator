# backend/api/digest/routes.py

from fastapi import (
    APIRouter,
    HTTPException,
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
)

from core.digest.html_service import (
    render_digest_html,
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
