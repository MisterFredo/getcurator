from typing import List

from utils.llm import run_llm

from core.workspace.context_service import (
    build_workspace_context,
)

from core.workspace.prompt_service import (
    build_key_points_prompt,
    build_structure_prompt,
    build_implications_prompt,
)

from core.user.user_profile_service import (
    get_user_profile,
)

# ============================================================
# OUTPUT TYPES
# ============================================================

OUTPUT_KEY_POINTS = "key_points"
OUTPUT_STRUCTURE = "structure"
OUTPUT_IMPLICATIONS = "implications"


# ============================================================
# BUILD PROMPT
# ============================================================

def build_prompt(
    output_type: str,
    context: dict,
) -> str:

    # ========================================================
    # KEY POINTS
    # ========================================================

    if output_type == OUTPUT_KEY_POINTS:
        return build_key_points_prompt(
            context
        )

    # ========================================================
    # STRUCTURE
    # ========================================================

    if output_type == OUTPUT_STRUCTURE:
        return build_structure_prompt(
            context
        )

    if output_type == OUTPUT_IMPLICATIONS:
        return build_implications_prompt(
            context
        )

    # ========================================================
    # UNKNOWN
    # ========================================================

    raise ValueError(
        f"Unknown output_type: {output_type}"
    )


# ============================================================
# GENERATE WORKSPACE OUTPUT
# ============================================================

def generate_workspace_output(
    output_type: str,

    content_ids: List[str] = None,
    number_ids: List[str] = None,
) -> str:

    content_ids = content_ids or []
    number_ids = number_ids or []

    # ========================================================
    # EMPTY
    # ========================================================

    if not content_ids and not number_ids:
        return ""

    # ========================================================
    # CONTEXT
    # ========================================================

    context = build_workspace_context(
        content_ids=content_ids,
        number_ids=number_ids,
    )

    # ========================================================
    # SAFETY
    # ========================================================

    if context.get("total_count", 0) == 0:
        return ""

    # ========================================================
    # PROMPT
    # ========================================================

    prompt = build_prompt(
        output_type=output_type,
        context=context,
    )

    # ========================================================
    # LLM
    # ========================================================

    result = run_llm(
        prompt=prompt,
        temperature=0.2,
    )

    # ========================================================
    # OUTPUT
    # ========================================================

    return result or ""
