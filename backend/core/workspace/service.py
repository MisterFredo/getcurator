# backend/core/workspace/service.py

from utils.llm import run_llm

from api.expertise.models import Expertise

from api.workspace.models import (
    WorkspaceNumber,
)

from core.expertise.service import (
    generate_expertise_from_contents,
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

from core.workspace.number_service import (
    load_numbers_by_ids,
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
    expertise: Expertise,
    numbers: list[WorkspaceNumber],
) -> str:

    # ========================================================
    # KEY POINTS
    # ========================================================

    if output_type == OUTPUT_KEY_POINTS:

        return build_key_points_prompt(
            expertise=expertise,
            numbers=numbers,
        )

    # ========================================================
    # STRUCTURE
    # ========================================================

    if output_type == OUTPUT_STRUCTURE:

        return build_structure_prompt(
            expertise=expertise,
            numbers=numbers,
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

    # ========================================================
    # EMPTY
    # ========================================================

    if not content_ids and not number_ids:
        return ""

    # ========================================================
    # EXPERTISE
    # ========================================================

    expertise = generate_expertise_from_contents(
        user_id=user_id,
        content_ids=content_ids,
    )

    if expertise.count == 0:
        return ""

    # ========================================================
    # NUMBERS
    # ========================================================

    numbers = load_numbers_by_ids(
        number_ids
    )

    # ========================================================
    # PROMPT
    # ========================================================

    prompt = build_prompt(
        output_type=output_type,
        expertise=expertise,
        numbers=numbers,
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
