from typing import Dict, List

from utils.llm import run_llm

from core.workspace.prompt_service import (
    build_key_points_prompt,
    build_implications_prompt,
)


# ============================================================
# SUMMARY
# ============================================================

def generate_digest_summary(
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

def generate_digest_implications(
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

def generate_digest_analysis(
    contents: List[Dict],
    profile_text: str,
) -> Dict:

    summary = generate_digest_summary(
        contents
    )

    implications = (
        generate_digest_implications(
            contents=contents,
            profile_text=profile_text,
        )
    )

    return {
        "summary": summary,
        "implications": implications,
    }

def generate_digest_analysis_from_ids(
    user_id: str,
    content_ids: List[str],
) -> Dict:
