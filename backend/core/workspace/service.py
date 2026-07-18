# backend/core/workspace/service.py

from core.delivery.models import (
    KnowledgeRequest,
)

from core.delivery.service import (
    deliver_knowledge,
)


# ============================================================
# GENERATE WORKSPACE OUTPUT
# ============================================================

def generate_workspace_output(
    output_type: str,
    content_ids: list[str] | None = None,
    number_ids: list[str] | None = None,
    user_id: str | None = None,
) -> str:

    content_ids = content_ids or []
    number_ids = number_ids or []

    if not user_id:
        raise ValueError(
            "user_id is required"
        )

    if not content_ids and not number_ids:
        return ""

    request = KnowledgeRequest(

        user_id=user_id,

        content_ids=content_ids,

        number_ids=number_ids,

        capabilities=[
            output_type,
        ],
    )

    result = deliver_knowledge(
        request
    )

    return result.outputs.get(
        output_type,
        "",
    )
