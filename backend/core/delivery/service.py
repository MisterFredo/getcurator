from core.delivery.models import (
    KnowledgeRequest,
    KnowledgeResult,
)

from core.expertise.service import (
    generate_expertise_from_contents,
)

from core.expertise.capability_service import (
    execute_capability,
)


# ============================================================
# DELIVER KNOWLEDGE
# ============================================================

def deliver_knowledge(
    request: KnowledgeRequest,
) -> KnowledgeResult:

    # ========================================================
    # BUILD EXPERTISE
    # ========================================================

    expertise = generate_expertise_from_contents(
        user_id=request.user_id,
        content_ids=request.content_ids,
    )

    # ========================================================
    # EXECUTE CAPABILITIES
    # ========================================================

    capability_results = {}

    for capability in request.capabilities:

        capability_results[capability] = execute_capability(
            expertise=expertise,
            capability=capability,
        )

    # ========================================================
    # RESULT
    # ========================================================

    return KnowledgeResult(
        expertise=expertise,
        capability_results=capability_results,
    )
