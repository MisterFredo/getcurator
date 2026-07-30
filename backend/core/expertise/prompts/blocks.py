from api.expertise.models import (
    ExpertiseContent,
)


# ============================================================
# CONTENT BLOCKS
# ============================================================

def build_content_blocks(
    contents: list[ExpertiseContent],
) -> str:
    """
    Convert the selected expertise contents into a structured textual
    context consumed by the Expertise prompts.

    The enriched analytical fields are presented first because they
    represent the synthesized knowledge extracted from each article.

    The original article remains available as supporting context.
    """

    if not contents:
        return "No content."

    blocks = []

    for index, c in enumerate(contents, start=1):

        figures = "\n".join(c.chiffres or [])

        block = f"""
CONTENT #{index}

SIGNAL:
{(c.signal or "").strip()}

MECHANISM:
{(c.mecanique or "").strip()}

STRATEGIC ISSUE:
{(c.enjeu or "").strip()}

FRICTION:
{(c.friction or "").strip()}

KEY FIGURES:
{figures}

--------------------------------------------------

SOURCE CONTEXT

TITLE:
{(c.title or "").strip()}

EXCERPT:
{(c.excerpt or "").strip()}

CONTENT:
{(c.content_body or "").strip()}
"""

        blocks.append(
            block.strip()
        )

    return "\n\n==================================================\n\n".join(
        blocks
    )
