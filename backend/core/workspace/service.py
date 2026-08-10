# backend/core/workspace/service.py

from core.delivery.models import (
    KnowledgeRequest,
)

from core.expertise.service import (
    generate_knowledge,
)


# ============================================================
# GENERATE WORKSPACE OUTPUT
# ============================================================

def generate_workspace_output(
    capability: str,
    content_ids: list[str] | None = None,
    number_ids: list[str] | None = None,
    user_id: str | None = None,
) -> str:

    if not user_id:

        raise ValueError(
            "user_id is required",
        )

    content_ids = content_ids or []

    number_ids = number_ids or []

    if not content_ids and not number_ids:

        return ""

    knowledge = generate_knowledge(

        KnowledgeRequest(

            user_id=user_id,

            content_ids=content_ids,

            number_ids=number_ids,

            capabilities=[
                capability,
            ],

        )

    )

    return knowledge.capability_results.get(

        capability,

        "",

    )
