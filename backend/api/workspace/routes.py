from fastapi import APIRouter

from api.workspace.models import (
    WorkspaceGenerateRequest,
)

from core.workspace.service import (
    generate_workspace_output,
)

router = APIRouter()


# ============================================================
# GENERATE
# ============================================================

@router.post("/generate")
def generate_workspace(
    payload: WorkspaceGenerateRequest,
):

    result = generate_workspace_output(
        output_type=payload.output_type,

        content_ids=payload.content_ids,

        number_ids=payload.number_ids,
    )

    return {
        "status": "ok",
        "result": result,
    }
