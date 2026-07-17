from typing import Dict, List


# ============================================================
# CONTENT BLOCKS
# ============================================================

def build_content_blocks(
    contents: List[Dict],
) -> str:

    if not contents:
        return "Aucun contenu."

    blocks = []

    for c in contents:

        block = f"""
TITRE:
{c.get("title")}

CONTENU:
{c.get("content_body")}

SIGNAL:
{c.get("signal")}

MECANIQUE:
{c.get("mecanique")}

ENJEU:
{c.get("enjeu")}

FRICTION:
{c.get("friction")}

CHIFFRES:
{c.get("chiffres")}
"""

        blocks.append(
            block.strip()
        )

    return "\n\n====================\n\n".join(
        blocks
    )


def build_implications_prompt(
    context: Dict,
) -> str:

    contents = context.get(
        "contents",
        [],
    )

    profile_text = context.get(
        "profile_text",
        "",
    )

    content_context = (
        build_content_blocks(
            contents
        )
    )

    return f"""
You are a business intelligence analyst.

Your role is not to summarize content.

The content has already been selected.

Your role is to explain why these signals matter for a specific expert profile.

--------------------------------------------------
LANGUAGE REQUIREMENT

Your entire response MUST be written in English.

All headings, bullets and explanations must be in English.

Never answer in French.

--------------------------------------------------
EXPERT PROFILE

{profile_text}

--------------------------------------------------
CONTENTS

{content_context}

--------------------------------------------------
OBJECTIVE

Explain what the selected signals collectively mean for this expert profile.

The content has already been filtered and selected.

Do not explain individual articles.

Do not rank articles.

Do not summarize content.

Focus on significance and implications.

--------------------------------------------------
TASK

1. Identify recurring patterns across the selected signals.
2. Explain why these patterns matter for the expert profile.
3. Connect multiple signals together when they point to the same trend.
4. Highlight what these signals collectively suggest.
5. Focus on implications derived from the provided content only.

--------------------------------------------------
OUTPUT FORMAT

KEY IMPLICATIONS

- implication
    Explanation
- implication
    Explanation
- implication
    Explanation

--------------------------------------------------
RULES

- Maximum 5 implications
- Each implication must contain: a short implication title and a concise explanation of why it matters for the expert profile
- No article-by-article summary
- No filler
- No generic statements
- No invention
- Use only the provided content
- Base every implication on the selected signals
- Connect signals whenever possible
- Explain significance, not strategy
- Do not recommend actions
- Do not speculate about future outcomes
- Do not invent opportunities or risks

--------------------------------------------------

You are an analyst, not a reporter.

Your role is to explain why the selected signals matter for this profile.
""".strip()
