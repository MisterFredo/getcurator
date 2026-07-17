from typing import Dict, List

from core.llm.service import run_llm

from .prompt_service import (
    build_key_points_prompt,
)

from .prompt_service import (
    build_implications_prompt,
)


# ============================================================
# GENERATE SUMMARY
# ============================================================

def generate_summary(
    contents: List[Dict],
) -> str:

    if not contents:
        return ""

    prompt = build_key_points_prompt(
        contents=contents,
    )

    return run_llm(
        prompt=prompt,
        temperature=0.2,
    )


# ============================================================
# GENERATE IMPLICATIONS
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

    return run_llm(
        prompt=prompt,
        temperature=0.2,
    )


# ============================================================
# IMPLICATIONS
# ============================================================

def generate_implications(
    contents: List[Dict],
    profile_text: str,
) -> str:

    if not contents:
        return ""

    context = {
        "contents": contents,
        "profile_text": (
            profile_text
            or "Generic business professional"
        ),
    }

    prompt = build_implications_prompt(
        context
    )

    result = run_llm(
        prompt=prompt,
        temperature=0.2,
    )

    return result or ""


# ============================================================
# FULL ANALYSIS
# ============================================================

def generate_insights(
    contents: List[Dict],
    profile_text: str,
) -> Dict:

    summary = generate_summary(
        contents
    )

    implications = (
        generate_implications(
            contents=contents,
            profile_text=profile_text,
        )
    )

    return {
        "summary": summary,
        "implications": implications,
    }


