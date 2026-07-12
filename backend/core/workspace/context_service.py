from typing import List, Dict


from core.numbers.insight_service import (
    get_numbers_by_ids,
)


# ============================================================
# BUILD WORKSPACE CONTEXT
# ============================================================

def build_workspace_context(
    content_ids: List[str] = None,
    number_ids: List[str] = None,
) -> Dict:

    content_ids = content_ids or []
    number_ids = number_ids or []



    # ========================================================
    # NUMBERS
    # ========================================================

    numbers = get_numbers_by_ids(
        number_ids
    )

    # ========================================================
    # OUTPUT
    # ========================================================

    return {
        "contents": contents,
        "numbers": numbers,

        "content_count": len(contents),
        "number_count": len(numbers),

        "total_count":
            len(contents) + len(numbers),
    }
