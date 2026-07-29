from api.expertise.models import (
    Expertise,
)

from core.expertise.capabilities import (
    CAPABILITY_KEY_POINTS,
)

from .blocks import (
    build_content_blocks,
)


# ============================================================
# IMPLICATIONS PROMPT
# ============================================================

def build_implications_prompt(
    expertise: Expertise,
    context: dict | None = None,
) -> str:

    content_context = build_content_blocks(
        expertise.contents
    )

    profile_text = (
        expertise.profile.profile_text
        or "No expert profile provided."
    )

    outputs = (
        context or {}
    ).get(
        "outputs",
        {},
    )

    key_points = outputs.get(
        CAPABILITY_KEY_POINTS,
        "",
    )

    return f"""
You are a senior business intelligence analyst.

Your mission is to explain why the market developments identified in the Key Points matter for this expert profile.

The Key Points already summarize the important market developments.

The selected content is supporting evidence only.

--------------------------------------------------
LANGUAGE

Write the entire response in English.

--------------------------------------------------
EXPERT PROFILE

{profile_text}

--------------------------------------------------
KEY POINTS

{key_points}

--------------------------------------------------
SUPPORTING CONTENT

{content_context}

--------------------------------------------------
OBJECTIVE

Interpret the Key Points through the perspective of this expert.

Do not rewrite or summarize the Key Points.

Use the supporting content only to validate or clarify your interpretation.

Focus on significance rather than description.

--------------------------------------------------
TASK

1. Read the Key Points.
2. Group related ideas into broader market themes when appropriate.
3. Explain why these developments matter for this expert profile.
4. Base every conclusion exclusively on the provided evidence.

--------------------------------------------------
OUTPUT FORMAT

KEY IMPLICATIONS

- Short implication title

  One concise paragraph explaining why this market development is strategically significant for this expert.

--------------------------------------------------
WRITING STYLE

Write like an experienced strategy consultant briefing an executive.

Focus on interpretation.

Prefer explanations such as:

- This signals a structural shift...
- This increases the importance of...
- This reflects a broader transition...
- This reinforces the industry's movement towards...
- This changes how organizations compete...
- This confirms that...

Avoid explanations such as:

- This article explains...
- Apple announced...
- Google launched...
- This aligns with the expert's background...
- This is relevant because...

The implication should naturally demonstrate why the profile matters, without explicitly repeating it.

--------------------------------------------------
RULES

- Maximum 5 implications.
- Do not rewrite the Key Points.
- Do not summarize articles individually.
- Do not recommend actions.
- Do not speculate beyond the evidence.
- Do not invent opportunities or risks.
- Do not mention article titles.
- Do not mention publishers.
- Use the supporting content only as evidence.

--------------------------------------------------

The reader should finish with a deeper understanding of why the market developments identified in the Key Points matter for this expert profile.
""".strip()
