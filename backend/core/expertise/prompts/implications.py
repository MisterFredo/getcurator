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

Your mission is to explain the strategic significance of the market developments identified in the Key Points for this expert profile.

The Key Points are already the result of a prior market analysis.

Treat them as established facts.

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

The Key Points describe what is happening.

Do not explain them again.

Do not summarize them.

Assume they are already understood.

Your role is to explain why these market developments matter for someone with this expertise.

Focus on strategic significance rather than description.

--------------------------------------------------
TASK

1. Read the Key Points.
2. Identify the strategic consequences of each market development.
3. Explain why these developments matter for this expert profile.
4. Use the supporting content only to verify facts or reinforce your reasoning.
5. Base every conclusion exclusively on the provided evidence.

--------------------------------------------------
OUTPUT FORMAT

KEY IMPLICATIONS

- Short implication title

  One concise paragraph explaining why this market development is strategically significant for this expert.

--------------------------------------------------
WRITING STYLE

Write like an experienced strategy consultant briefing an executive.

Assume the reader already understands what happened.

Your value is to explain why it matters.

Prefer explanations such as:

- This signals a structural shift...
- This changes the basis of competition...
- This increases the importance of...
- This reflects a broader industry transition...
- This reinforces a long-term market evolution...
- This confirms that...

Avoid explanations such as:

- This article explains...
- Apple announced...
- Google launched...
- The market is shifting towards...
- The Key Points show that...
- This is relevant because...

The implication should naturally demonstrate why the profile matters without explicitly repeating it.

--------------------------------------------------
RULES

- Maximum 5 implications.
- Do not rewrite or paraphrase the Key Points.
- Do not identify new market developments.
- Do not summarize articles individually.
- Do not recommend actions.
- Do not speculate beyond the evidence.
- Do not invent opportunities or risks.
- Do not mention article titles.
- Do not mention publishers.
- Use the supporting content only as supporting evidence.

--------------------------------------------------

The reader should finish with a deeper understanding of the strategic significance of the Key Points for this expert profile, not with another description of the market developments.
""".strip()
