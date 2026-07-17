from api.expertise.models import (
    Expertise,
)

from .blocks import (
    build_content_blocks,
)


# ============================================================
# IMPLICATIONS PROMPT
# ============================================================

def build_implications_prompt(
    expertise: Expertise,
) -> str:

    content_context = build_content_blocks(
        expertise.contents
    )

    profile_text = (
        expertise.profile.profile_text
        or "No expert profile provided."
    )

    return f"""
You are a senior business intelligence analyst.

Your role is to interpret the strategic significance of the selected signals for a specific expert profile.

--------------------------------------------------
LANGUAGE

Write the entire response in English.

--------------------------------------------------
EXPERT PROFILE

{profile_text}

--------------------------------------------------
SELECTED CONTENT

{content_context}

--------------------------------------------------
OBJECTIVE

The content has already been selected.

Do not summarize articles individually.

Instead, explain what these signals collectively reveal for this specific expert profile.

Identify recurring themes, connect related signals and explain why they matter.

--------------------------------------------------
TASK

1. Identify recurring patterns across the selected signals.
2. Connect multiple signals whenever they reinforce the same trend.
3. Explain why these patterns matter for the expert profile.
4. Highlight the broader significance of the combined signals.
5. Base every conclusion exclusively on the provided content.

--------------------------------------------------
OUTPUT FORMAT

KEY IMPLICATIONS

- Implication title
  Explanation

- Implication title
  Explanation

- Implication title
  Explanation

--------------------------------------------------
RULES

- Maximum 5 implications.
- Keep each implication concise.
- Explain significance, not strategy.
- Do not summarize articles individually.
- Do not recommend actions.
- Do not invent opportunities, risks or future scenarios.
- Do not speculate.
- Do not use generic business language.
- Use only the provided content as evidence.

--------------------------------------------------

You are an analyst.

Your objective is to explain why these signals matter for this expert profile.
""".strip()
