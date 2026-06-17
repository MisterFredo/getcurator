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


# ============================================================
# NUMBER BLOCKS
# ============================================================

def build_number_blocks(
    numbers: List[Dict],
) -> str:

    if not numbers:
        return "Aucun chiffre."

    blocks = []

    for n in numbers:

        block = f"""
LABEL:
{n.get("label")}

VALUE:
{n.get("value")} {n.get("unit")} {n.get("scale")}

TYPE:
{n.get("type")}

CATEGORY:
{n.get("category")}

ZONE:
{n.get("zone")}

PERIOD:
{n.get("period")}

ENTITY:
{n.get("entity_label")}
"""

        blocks.append(
            block.strip()
        )

    return "\n\n-----------------\n\n".join(
        blocks
    )


# ============================================================
# KEY POINTS PROMPT
# ============================================================

def build_key_points_prompt(
    context: Dict,
) -> str:

    contents = context.get(
        "contents",
        [],
    )

    numbers = context.get(
        "numbers",
        [],
    )

    content_context = (
        build_content_blocks(
            contents
        )
    )

    number_context = (
        build_number_blocks(
            numbers
        )
    )

    return f"""
You are a FACTUAL SYNTHESIS assistant for a business professional.

You work on already structured signals.

Do NOT interpret.
Do NOT invent.
Do NOT speculate.

You must prioritize and organize information.

--------------------------------------------------
LANGUAGE REQUIREMENT

Your entire response MUST be written in English.

All headings, bullets and explanations must be in English.

Never answer in French.

--------------------------------------------------
OBJECTIVE

Help a professional save time.

They do not want to read every content item.

They want to understand what truly matters.

--------------------------------------------------
CONTENTS
{content_context}

--------------------------------------------------
NUMBERS
{number_context}

--------------------------------------------------
TASK

1. Identify recurring signals
2. Prioritize important information
3. Connect numbers to trends
4. Group similar information
5. Extract useful business facts

--------------------------------------------------
OUTPUT FORMAT

TOP 5

- [CONCEPT] → fact + number

NOTABLE

- [CONCEPT] → secondary fact

--------------------------------------------------
RULES

- Maximum 5 TOP 5 items
- Maximum 5 NOTABLE items
- No storytelling
- No article-by-article summaries
- No filler
- No invention
- Group similar signals
- Prioritize business relevance

You are a business filter, not a writer.
""".strip()


# ============================================================
# STRUCTURE PROMPT
# ============================================================

def build_structure_prompt(
    context: Dict,
) -> str:

    contents = context.get(
        "contents",
        [],
    )

    numbers = context.get(
        "numbers",
        [],
    )

    content_context = (
        build_content_blocks(
            contents
        )
    )

    number_context = (
        build_number_blocks(
            numbers
        )
    )

    return f"""
You are a BUSINESS DATA assistant.

You work on already selected information.

Do NOT invent.
Do NOT speculate.

Your role is to structure information.

--------------------------------------------------
LANGUAGE REQUIREMENT

Your entire response MUST be written in English.

All headings, bullets and explanations must be in English.

Never answer in French.

--------------------------------------------------
OBJECTIVE

Transform multiple signals into:

1. a logical structure
2. a presentation order
3. a clear business narrative

--------------------------------------------------
CONTENTS
{content_context}

--------------------------------------------------
NUMBERS
{number_context}

--------------------------------------------------
TASK

1. Group information by business logic
2. Identify key dimensions:
   - scale
   - growth
   - performance
   - market signals
3. Organize information:
   - from strategic to operational
4. Use content to contextualize numbers
5. Build a structure that can be consumed quickly

--------------------------------------------------
OUTPUT FORMAT

STRUCTURE

- Block → theme + rationale
  - information
  - information

READING

- what the data is showing
- no storytelling
- no free interpretation

--------------------------------------------------
RULES

- No summary
- No filler
- No invention
- Structure and organization only
- Group similar information

You are an organization tool, not an analyst.
""".strip()
