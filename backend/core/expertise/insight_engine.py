
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
