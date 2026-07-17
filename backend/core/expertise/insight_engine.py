from typing import Dict, List

from utils.llm import run_llm

from core.expertise.prompt_service import (
    build_key_points_prompt,
    build_implications_prompt,
)

from core.insight.service import (
    get_analysis_details_by_ids,
)

from core.user.user_service import (
    get_user_context,
)


# ============================================================
# SUMMARY
# ============================================================

def generate_summary(
    contents: List[Dict],
) -> str:

    if not contents:
        return ""

    context = {
        "contents": contents,
        "numbers": [],
    }

    prompt = build_key_points_prompt(
        context
    )

    result = run_llm(
        prompt=prompt,
        temperature=0.2,
    )

    return result or ""


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


