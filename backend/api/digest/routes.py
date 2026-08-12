# backend/api/digest/routes.py

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    Query,
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
    list_digest_history,
    search_digests,
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
        "user_id": user_id,
        "digests": list_digest_history(
            user_id,
        ),
    }


# ============================================================
# PUBLIC DIGESTS — USER / EXPERT
# ============================================================

@router.get(
    "/users/{target_user_id}",
)
def list_user_digests_route(
    target_user_id: str,
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
    # OWN DIGESTS
    # ========================================================

    if target_user_id == user_id:

        return {
            "status": "ok",
            "user_id": target_user_id,
            "digests": list_digest_history(
                target_user_id,
            ),
        }

    # ========================================================
    # SELECTED EXPERTS
    # ========================================================

    experts = get_user_experts(
        user_id,
    )

    allowed = any(

        expert.get("ID_USER")
            == target_user_id

        and expert.get(
            "IS_SELECTED"
        )

        for expert in experts

    )

    if not allowed:

        raise HTTPException(
            status_code=403,
            detail="User not available",
        )

    return {
        "status": "ok",
        "user_id": target_user_id,
        "digests": list_digest_history(
            target_user_id,
        ),
    }

# ============================================================
# PUBLIC DIGESTS — SEARCH
# ============================================================

@router.get("/search")
def search_digests_route(
    request: Request,

    query: str | None = Query(
        default=None,
    ),

    user_id: str | None = Query(
        default=None,
    ),

    company_id: str | None = Query(
        default=None,
    ),

    solution_id: str | None = Query(
        default=None,
    ),

    topic_id: str | None = Query(
        default=None,
    ),
):

    # ========================================================
    # AUTH
    # ========================================================

    current_user_id = (
        get_user_id_from_request(
            request,
        )
    )

    if not current_user_id:

        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    # ========================================================
    # SEARCH
    # ========================================================

    digests = search_digests(

        query=query,

        user_id=user_id,

        company_id=company_id,

        solution_id=solution_id,

        topic_id=topic_id,

    )

    # ========================================================
    # RETURN
    # ========================================================

    return {
        "status": "ok",
        "digests": digests,
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
