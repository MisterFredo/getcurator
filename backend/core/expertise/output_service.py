# backend/core/expertise/output_service.py

from utils.llm import run_llm

from api.expertise.models import (
    Expertise,
)

from core.expertise.prompts.key_points import (
    build_key_points_prompt,
)

from core.expertise.prompts.structure import (
    build_structure_prompt,
)

from core.expertise.prompts.implications import (
    build_implications_prompt,
)

# ============================================================
# OUTPUT TYPES
# ============================================================

from core.expertise.constants import (
    OUTPUT_KEY_POINTS,
    OUTPUT_STRUCTURE,
    OUTPUT_IMPLICATIONS,
)

# ============================================================
# BUILD PROMPT
# ============================================================

def _build_prompt()
    output_type: str,
    expertise: Expertise,
) -> str:

    # ========================================================
    # KEY POINTS
    # ========================================================

    if output_type == OUTPUT_KEY_POINTS:

        return build_key_points_prompt(
            expertise=expertise,
        )

    # ========================================================
    # STRUCTURE
    # ========================================================

    if output_type == OUTPUT_STRUCTURE:

        return build_structure_prompt(
            expertise=expertise,
        )

    # ========================================================
    # IMPLICATIONS
    # ========================================================

    if output_type == OUTPUT_IMPLICATIONS:

        return build_implications_prompt(
            expertise=expertise,
        )

    # ========================================================
    # UNKNOWN
    # ========================================================

    raise ValueError(
        f"Unknown output_type: {output_type}"
    )


# ============================================================
# GENERATE OUTPUT
# ============================================================

def generate_expertise_output(
    expertise: Expertise,
    output_type: str,
) -> str:

    if expertise.count == 0:
        return ""

    # ========================================================
    # PROMPT
    # ========================================================

    prompt = build_prompt(
        output_type=output_type,
        expertise=expertise,
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
