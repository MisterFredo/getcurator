# backend/core/expertise/capability_service.py

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

from core.expertise.capabilities import (
    CAPABILITY_KEY_POINTS,
    CAPABILITY_STRUCTURE,
    CAPABILITY_IMPLICATIONS,
)


# ============================================================
# BUILD PROMPT
# ============================================================

def _build_prompt(
    capability: str,
    expertise: Expertise,
) -> str:

    # ========================================================
    # KEY POINTS
    # ========================================================

    if capability == CAPABILITY_KEY_POINTS:

        return build_key_points_prompt(
            expertise=expertise,
        )

    # ========================================================
    # STRUCTURE
    # ========================================================

    if capability == CAPABILITY_STRUCTURE:

        return build_structure_prompt(
            expertise=expertise,
        )

    # ========================================================
    # IMPLICATIONS
    # ========================================================

    if capability == CAPABILITY_IMPLICATIONS:

        return build_implications_prompt(
            expertise=expertise,
        )

    # ========================================================
    # UNKNOWN
    # ========================================================

    raise ValueError(
        f"Unknown capability: {capability}"
    )


# ============================================================
# EXECUTE CAPABILITY
# ============================================================

def execute_capability(
    expertise: Expertise,
    capability: str,
) -> str:

    if expertise.count == 0:
        return ""

    # ========================================================
    # PROMPT
    # ========================================================

    prompt = _build_prompt(
        capability=capability,
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
    # RESULT
    # ========================================================

    return result or ""
