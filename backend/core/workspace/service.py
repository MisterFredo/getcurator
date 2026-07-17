# backend/core/workspace/service.py

from core.expertise.output_service import (
    generate_expertise_output,
)

from core.expertise.service import (
    generate_expertise_from_contents,
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
    # VALIDATION
    # ========================================================

    if not user_id:
        raise ValueError(
            "user_id is required"
        )

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
    # OUTPUT
    # ========================================================

    return generate_expertise_output(

        expertise=expertise,

        output_type=output_type,

    )
