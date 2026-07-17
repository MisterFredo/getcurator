# backend/core/expertise/service.py

from typing import Dict

from .profile_service import (
    load_profile,
)

from .selection_engine import (
    select_contents,
)

from .insight_engine import (
    generate_insights,
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

    profile = load_profile(
        user_id=user_id,
    )

    contents = select_contents(
        profile=profile,
        period_start=period_start,
        period_end=period_end,
        limit=limit,
    )

    return {

        "profile": profile,

        "contents": contents,

        "count": len(contents),
    }


# ============================================================
# GENERATE EXPERTISE INSIGHTS
# ============================================================

def generate_expertise_insights(
    context: Dict,
) -> Dict:

    insights = generate_insights(
        profile=context["profile"],
        contents=context["contents"],
    )

    return {

        **context,

        **insights,
    }


# ============================================================
# GENERATE EXPERTISE
# ============================================================

def generate_expertise(
    user_id: str,
    period_start: str | None = None,
    period_end: str | None = None,
    limit: int | None = None,
) -> Dict:

    context = generate_expertise_context(
        user_id=user_id,
        period_start=period_start,
        period_end=period_end,
        limit=limit,
    )

    return generate_expertise_insights(
        context,
    )
