from typing import Dict

from .profile_service import (
    load_profile,
)

from .selection_engine import (
    select_contents,
)


# ============================================================
# GENERATE EXPERTISE CONTEXT
# ============================================================

def generate_expertise_context(
    user_id: str,
    period_start: str | None = None,
    period_end: str | None = None,
    limit: int | None = None,
) -> Dict:

    # ========================================================
    # LOAD PROFILE
    # ========================================================

    profile = load_profile(
        user_id=user_id,
    )

    # ========================================================
    # SELECT CONTENTS
    # ========================================================

    contents = select_contents(
        profile=profile,
        period_start=period_start,
        period_end=period_end,
        limit=limit,
    )

    # ========================================================
    # RESULT
    # ========================================================

    return {

        "profile": profile,

        "contents": contents,

        "count": len(contents),
    }
