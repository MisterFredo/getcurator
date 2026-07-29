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

Your mission is to identify the structural market developments emerging from a curated set of business content.

The articles are evidence.

Your output is NOT about the articles.

Your output is about what is happening in the market.

--------------------------------------------------
LANGUAGE

Write the entire response in English.

--------------------------------------------------
OBJECTIVE

Identify the most important market developments emerging from the selected content.

Each Key Point should describe a market development that can be interpreted independently by subsequent analytical capabilities.

Focus on trends, structural shifts, emerging patterns and market evolutions.

Do not describe individual news stories.
--------------------------------------------------
SELECTED CONTENT

{content_context}

--------------------------------------------------
TASK

1. Read every content item.
2. Look across all articles rather than treating them independently.
3. Identify recurring themes and common directions.
4. Merge multiple articles describing the same evolution.
5. Prioritize the developments with the greatest strategic significance.
6. Express each finding as a market evolution rather than an event.

--------------------------------------------------
OUTPUT FORMAT

KEY MARKET DEVELOPMENTS

- One concise statement describing a major market development.

SECONDARY DEVELOPMENTS

- One concise statement describing a secondary market development.

--------------------------------------------------
WRITING STYLE

Write like an analyst presenting findings to executives.

Prefer sentences such as:

- The market is shifting towards...
- Publishers are increasingly...
- Brands are moving away from...
- Privacy requirements are accelerating...
- Retail media is becoming...
- Browser vendors are consolidating...

Avoid sentences such as:

- Apple announced...
- Google launched...
- Company X introduced...
- An article explains...

--------------------------------------------------
RULES

- Maximum 5 TOP 5 items.
- Maximum 5 NOTABLE items.
- One market development per bullet.
- Merge related evidence into one finding.
- Never produce one bullet per article.
- Focus on the market, not individual companies.
- Mention companies only when they genuinely represent a broader market movement.
- Remove duplication.
- Keep every statement factual.
- Do not explain why the development matters.
- Do not make recommendations.
- Do not speculate beyond the evidence.
- Do not mention article titles.
- Do not mention publishers.
- Use only the provided content.
- Each Key Point should be self-contained and understandable without referring back to the original articles.

--------------------------------------------------

The reader should finish with a clear understanding of the few market developments that deserve attention this week, not with a list of article summaries.
""".strip()
