from core.delivery.models import (
    KnowledgeRequest,
    KnowledgeResult,
)

from core.expertise.service import (
    generate_expertise_from_contents,
)

from core.expertise.output_service import (
    generate_expertise_output,
)


# ============================================================
# DELIVER KNOWLEDGE
# ============================================================

def deliver_knowledge(
    request: KnowledgeRequest,
) -> KnowledgeResult:

    expertise = generate_expertise_from_contents(

        user_id=request.user_id,

        content_ids=request.content_ids,

    )

    outputs = {}

    for capability in request.capabilities:

        outputs[capability] = (
            generate_expertise_output(
                expertise=expertise,
                output_type=capability,
            )
        )

    return KnowledgeResult(

        expertise=expertise,

        outputs=outputs,
    )
