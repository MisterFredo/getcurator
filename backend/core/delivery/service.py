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

from core.expertise.capabilities import (
    CAPABILITY_KEY_POINTS,
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
    # CONTEXT
    # ========================================================

    capability_results: dict[str, str] = {}

    context = {
        "outputs": {},
    }

    # ========================================================
    # KEY POINTS FIRST
    # ========================================================

    if CAPABILITY_KEY_POINTS in request.capabilities:

        result = execute_capability(

            expertise=expertise,

            capability=CAPABILITY_KEY_POINTS,

            context=context,

        )

        capability_results[
            CAPABILITY_KEY_POINTS
        ] = result

        context["outputs"][
            CAPABILITY_KEY_POINTS
        ] = result

    # ========================================================
    # OTHER CAPABILITIES
    # ========================================================

    for capability in request.capabilities:

        if capability == CAPABILITY_KEY_POINTS:

            continue

        result = execute_capability(

            expertise=expertise,

            capability=capability,

            context=context,

        )

        capability_results[
            capability
        ] = result

        context["outputs"][
            capability
        ] = result

    # ========================================================
    # RESULT
    # ========================================================

    return KnowledgeResult(

        expertise=expertise,

        capability_results=capability_results,

    )
