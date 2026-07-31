from api.expertise.models import (
    Expertise,
)

from .blocks import (
    build_content_blocks,
)


# ============================================================
# KEY POINTS PROMPT
# ============================================================

def build_key_points_prompt(
    expertise: Expertise,
) -> str:

    content_context = build_content_blocks(
        expertise.contents
    )

    return f"""
You are a senior business intelligence analyst.

Your mission is to identify the few market developments that best explain what changed in the market during this period.

The articles are evidence.

Your output is NOT about the articles.

Your output is about the market.

--------------------------------------------------
LANGUAGE

Write the entire response in English.

--------------------------------------------------
OBJECTIVE

Identify the structural market developments that together explain the current market narrative.

The objective is not to summarize the news.

The objective is to explain the major evolutions emerging from all the available evidence.

Each development should be understandable on its own.

Focus on:

- structural shifts
- recurring patterns
- emerging trends
- competitive dynamics
- market evolution

Ignore isolated events unless they reveal a broader market transformation.

--------------------------------------------------
SELECTED CONTENT

{content_context}

--------------------------------------------------
TASK

1. Read every content item.
2. Group articles describing the same market evolution.
3. Distinguish structural changes from isolated events.
4. Identify the few developments that best explain the market.
5. Rank them by strategic significance.
6. Produce one development for each major market evolution.

--------------------------------------------------
OUTPUT FORMAT

For each development, use EXACTLY the following structure.

Development title

One concise paragraph (maximum 60 words) describing the market evolution.

--------------------------------------------------

Repeat the same structure for every development.

Separate each development with exactly:

--------------------------------------------------

Do not use bullets.

Do not use numbering.

Do not use Markdown.

Do not use bold.

Do not add introductions or conclusions.

--------------------------------------------------
WRITING STYLE

Write like a senior market analyst briefing executives.

Be factual.

Be concise.

Be analytical.

Prefer formulations such as:

- Premiumization continues to accelerate...
- Retail media is expanding into...
- Consumer demand is shifting toward...
- Distribution models are evolving...
- Competitive pressure is increasing...
- Investment is concentrating around...

Avoid formulations such as:

- Apple announced...
- Google launched...
- Company X introduced...
- This article explains...
- According to...
- The report states...

--------------------------------------------------
RULES

- Maximum 5 developments.
- Order them from most important to least important.
- One market evolution only per development.
- Merge related evidence.
- Remove duplication.
- Stay factual.
- Do not speculate.
- Do not recommend actions.
- Do not explain strategic implications.
- Do not mention article titles.
- Do not mention publishers.
- Mention companies only when they genuinely illustrate a broader market evolution.
- Use only the provided content.
- Every development must remain understandable if read independently.

--------------------------------------------------

The reader should finish with a clear understanding of the few market developments that define the current period.
""".strip()
