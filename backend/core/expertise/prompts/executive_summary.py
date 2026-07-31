from core.expertise.capabilities import (
    CAPABILITY_KEY_POINTS,
)


# ============================================================
# EXECUTIVE SUMMARY PROMPT
# ============================================================

def build_executive_summary_prompt(
    context: dict | None = None,
) -> str:

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

Your mission is to write a concise Executive Summary of the market developments already identified in the Key Points.

The Key Points are established market facts.

Do not question them.

Do not reinterpret them.

Do not introduce new ideas.

Your role is to help an executive understand the overall story of this period in less than one minute.

--------------------------------------------------
LANGUAGE

Write the entire response in English.

--------------------------------------------------
KEY POINTS

{key_points}

--------------------------------------------------
OBJECTIVE

Produce a short narrative that summarizes the overall direction of the market.

The Executive Summary should answer one question:

"What is the story of this period?"

Do not list the Key Points.

Connect them naturally into one coherent narrative.

Highlight the dominant themes and explain how they fit together.

--------------------------------------------------
TASK

1. Read every Key Point.
2. Identify the common direction they reveal.
3. Build one coherent narrative.
4. Explain the overall market trajectory.
5. Remain strictly faithful to the Key Points.

--------------------------------------------------
OUTPUT FORMAT

Write only the Executive Summary.

Use 2 or 3 short paragraphs.

Each paragraph should contain 1 or 2 sentences.

Maximum 120 words.

Leave one blank line between paragraphs.

--------------------------------------------------
WRITING STYLE

Write like the opening section of an executive market briefing.

Be concise.

Be analytical.

Be highly readable.

Prefer formulations such as:

- This period confirms...
- The market continues to...
- Several developments indicate...
- Together these developments suggest...
- The overall direction points toward...

Avoid formulations such as:

- The Key Points show...
- This report explains...
- The articles indicate...
- According to...
- Company X announced...

--------------------------------------------------
RULES

- Return only the summary text.
- Do not write a title.
- Do not write "Executive Summary".
- Use 2 or 3 short paragraphs.
- No bullet points.
- No headings.
- No recommendations.
- No strategic implications.
- No speculation.
- No new market developments.
- Use only the information contained in the Key Points.
- Do not mention articles or publishers.

--------------------------------------------------

The reader should understand the overall direction of the market after reading this Executive Summary, before exploring the Key Points in detail.
""".strip()
