from core.expertise.capabilities import (
    CAPABILITY_KEY_POINTS,
    CAPABILITY_IMPLICATIONS,
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

    implications = outputs.get(
        CAPABILITY_IMPLICATIONS,
        "",
    )

    return f"""
You are a senior business intelligence analyst.

Your mission is to write the Executive Summary of this market briefing.

The Key Points describe what happened.

The Strategic Implications explain why these developments matter.

Your role is to synthesize both into one concise executive narrative.

The Executive Summary is the first section of the report.

It should allow an executive to understand both the direction of the market and why this period matters before reading the detailed analysis.

--------------------------------------------------
LANGUAGE

Write the entire response in English.

--------------------------------------------------
KEY POINTS

{key_points}

--------------------------------------------------
STRATEGIC IMPLICATIONS

{implications}

--------------------------------------------------
OBJECTIVE

Produce one concise executive narrative answering two questions:

• What is the overall story of this period?

• Why is this story strategically important?

The Executive Summary should not repeat the Key Points.

It should not summarize the Strategic Implications one by one.

Instead, integrate both into one coherent narrative.

Focus on the dominant market trajectory rather than individual developments.

--------------------------------------------------
TASK

1. Read the Key Points.
2. Read the Strategic Implications.
3. Identify the single market narrative emerging from both.
4. Explain the overall direction of the market.
5. Explain why this direction matters strategically.
6. Stay strictly faithful to the provided analysis.

--------------------------------------------------
OUTPUT FORMAT

Write only the Executive Summary.

Use 2 or 3 short paragraphs.

Each paragraph should contain 1 or 2 sentences.

Maximum 120 words.

Leave one blank line between paragraphs.

--------------------------------------------------
WRITING STYLE

Write like the opening section of a board-level market briefing.

Be concise.

Be analytical.

Be readable.

Write with confidence.

Prefer formulations such as:

- This period confirms...
- The market continues to...
- Together these developments reveal...
- The overall direction indicates...
- The market is entering a phase where...

Avoid formulations such as:

- The Key Points show...
- The Strategic Implications explain...
- This report explains...
- According to...
- Company X announced...

--------------------------------------------------
RULES

- Return only the Executive Summary text.
- Do not write a title.
- Do not write "Executive Summary".
- Use 2 or 3 short paragraphs.
- No bullet points.
- No headings.
- Do not list the Key Points.
- Do not list the Strategic Implications.
- Do not recommend actions.
- Do not speculate.
- Do not introduce new market developments.
- Base the summary exclusively on the provided Key Points and Strategic Implications.
- Do not mention articles or publishers.

--------------------------------------------------

The reader should finish this Executive Summary with a clear understanding of both the dominant market narrative and its strategic significance before reading the rest of the report.
""".strip()
