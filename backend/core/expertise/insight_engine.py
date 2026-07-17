# backend/core/expertise/insight_engine.py

from api.expertise.models import (
    ExpertiseContent,
    ExpertiseInsights,
    ExpertiseProfile,
)

from core.llm.service import (
    run_llm,
)

from .prompt_service import (
    build_implications_prompt,
    build_key_points_prompt,
)


# ============================================================
# RUN INSIGHT
# ============================================================

def _run_insight(
    prompt: str,
    temperature: float = 0.2,
) -> str:

    result = run_llm(
        prompt=prompt,
        temperature=temperature,
    )

    return result or ""


# ============================================================
# SUMMARY
# ============================================================

def generate_summary(
    contents: list[ExpertiseContent],
) -> str:

    if not contents:
        return ""

    prompt = build_key_points_prompt(
        contents=contents,
    )

    return _run_insight(
        prompt=prompt,
    )


# ============================================================
# IMPLICATIONS
# ============================================================

def generate_implications(
    profile: ExpertiseProfile,
    contents: list[ExpertiseContent],
) -> str:

    if not contents:
        return ""

    prompt = build_implications_prompt(

        contents=contents,

        profile_text=profile.profile_text,

    )

    return _run_insight(
        prompt=prompt,
    )


# ============================================================
# FULL INSIGHTS
# ============================================================

def generate_insights(
    profile: ExpertiseProfile,
    contents: list[ExpertiseContent],
) -> ExpertiseInsights:

    return ExpertiseInsights(

        summary=generate_summary(
            contents=contents,
        ),

        implications=generate_implications(
            profile=profile,
            contents=contents,
        ),
    )
