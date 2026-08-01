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
    CAPABILITY_EXECUTIVE_SUMMARY,
    CAPABILITY_KEY_POINTS,
    CAPABILITY_IMPLICATIONS,
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
    # KEY POINTS
    # ========================================================

    needs_key_points = any(

        capability in request.capabilities

        for capability in (

            CAPABILITY_KEY_POINTS,

            CAPABILITY_IMPLICATIONS,

            CAPABILITY_EXECUTIVE_SUMMARY,

        )

    )

    if needs_key_points:

        result = execute_capability(

            expertise=expertise,

            capability=CAPABILITY_KEY_POINTS,

            context=context,

        )

        context["outputs"][
            CAPABILITY_KEY_POINTS
        ] = result

        if CAPABILITY_KEY_POINTS in request.capabilities:

            capability_results[
                CAPABILITY_KEY_POINTS
            ] = result

    # ========================================================
    # STRATEGIC IMPLICATIONS
    # ========================================================

    if CAPABILITY_IMPLICATIONS in request.capabilities:

        result = execute_capability(

            expertise=expertise,

            capability=CAPABILITY_IMPLICATIONS,

            context=context,

        )

        context["outputs"][
            CAPABILITY_IMPLICATIONS
        ] = result

        capability_results[
            CAPABILITY_IMPLICATIONS
        ] = result

    # ========================================================
    # EXECUTIVE SUMMARY
    # ========================================================

    if CAPABILITY_EXECUTIVE_SUMMARY in request.capabilities:

        result = execute_capability(

            expertise=expertise,

            capability=CAPABILITY_EXECUTIVE_SUMMARY,

            context=context,

        )

        context["outputs"][
            CAPABILITY_EXECUTIVE_SUMMARY
        ] = result

        capability_results[
            CAPABILITY_EXECUTIVE_SUMMARY
        ] = result

    # ========================================================
    # REMAINING CAPABILITIES
    # ========================================================

    for capability in request.capabilities:

        if capability in (

            CAPABILITY_KEY_POINTS,

            CAPABILITY_IMPLICATIONS,

            CAPABILITY_EXECUTIVE_SUMMARY,

        ):

            continue

        result = execute_capability(

            expertise=expertise,

            capability=capability,

            context=context,

        )

        context["outputs"][
            capability
        ] = result

        capability_results[
            capability
        ] = result

    # ========================================================
    # RESULT
    # ========================================================

    return KnowledgeResult(

        expertise=expertise,

        capability_results=capability_results,

    )
