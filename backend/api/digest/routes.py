# backend/api/digest/routes.py

from fastapi import APIRouter

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
)

router = APIRouter()


# ============================================================
# CAMPAIGNS
# ============================================================

@router.post("/campaigns")
def create_campaign_route(
    request: CampaignCreateRequest,
):

    return create_campaign(
        request,
    )


@router.get("/campaigns")
def list_campaigns_route():

    return list_campaigns()


@router.get("/campaigns/{campaign_id}")
def get_campaign_route(
    campaign_id: str,
):

    return get_campaign(
        campaign_id,
    )


# ============================================================
# GENERATE
# ============================================================

@router.post("/campaigns/{campaign_id}/generate")
def generate_campaign_route(
    campaign_id: str,
):

    return generate_campaign(
        campaign_id,
    )


# ============================================================
# SEND
# ============================================================

@router.post("/campaigns/{campaign_id}/send")
def send_campaign_route(
    campaign_id: str,
):

    return send_campaign(
        campaign_id,
    )


# ============================================================
# DIGESTS
# ============================================================

@router.get("/digests/{digest_id}")
def get_digest_route(
    digest_id: str,
):

    return get_digest(
        digest_id,
    )
