# backend/core/delivery/service.py

from core.delivery.models import (
    KnowledgeRequest,
    KnowledgeResult,
)

from core.expertise.service import (
    generate_expertise_from_profile,
    generate_expertise_from_contents,
)

from core.expertise.capability_service import (
    execute_capability,
)

from api.expertise.models import (
    Expertise,
)


# ============================================================
# BUILD EXPERTISE
# ============================================================

def _build_expertise(
    request: KnowledgeRequest,
) -> Expertise:

    if request.content_ids:

        return generate_expertise_from_contents(
            user_id=request.user_id,
            content_ids=request.content_ids,
        )

    return generate_expertise_from_profile(
        user_id=request.user_id,
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

    if request.expertise is not None:

        expertise = request.expertise

    else:

        expertise = _build_expertise(
            request,
        )

    # ========================================================
    # EXECUTE CAPABILITIES
    # ========================================================

    capability_results: dict[str, str] = {}

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
