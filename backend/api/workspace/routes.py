from fastapi import (
    APIRouter,
    Request,
)

from api.workspace.models import (
    WorkspaceGenerateRequest,
)

from core.workspace.service import (
    generate_workspace_output,
)

from utils.auth import (
    get_user_id_from_request,
)

# ============================================================
# ROUTER
# ============================================================

router = APIRouter()


# ============================================================
# GENERATE
# ============================================================

@router.post("/generate")
def generate_workspace(
    request: Request,
    payload: WorkspaceGenerateRequest,
):

    user_id = get_user_id_from_request(
        request
    )

    result = generate_workspace_output(
        capability=payload.capability,
        content_ids=payload.content_ids,
        number_ids=payload.number_ids,
        user_id=user_id,
    )

    return {
        "status": "ok",
        "result": result,
    }
