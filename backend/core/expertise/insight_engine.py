# backend/core/expertise/insight_engine.py

from typing import Dict, List

from core.llm.service import run_llm

from .prompt_service import (
    build_key_points_prompt,
    build_implications_prompt,
)


# ============================================================
# INTERNAL
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
    contents: List[Dict],
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
    profile: Dict,
    contents: List[Dict],
) -> str:

    if not contents:
        return ""

    prompt = build_implications_prompt(
        contents=contents,
        profile_text=profile.get(
            "profile_text",
            "",
        ),
    )

    return _run_insight(
        prompt=prompt,
    )


# ============================================================
# FULL INSIGHTS
# ============================================================

def generate_insights(
    profile: Dict,
    contents: List[Dict],
) -> Dict:

    return {

        "summary": generate_summary(
            contents,
        ),

        "implications": generate_implications(
            profile=profile,
            contents=contents,
        ),
    }
