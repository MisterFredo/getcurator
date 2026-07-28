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
    Convert the selected expertise contents into a textual context
    consumed by the different Expertise prompts.
    """

    if not contents:
        return "No content."

    blocks = []

    for c in contents:

        block = f"""
TITLE:
{(c.title or "").strip()}

EXCERPT:
{(c.excerpt or "").strip()}

CONTENT:
{(c.content_body or "").strip()}

SIGNAL:
{(c.signal or "").strip()}

MECHANISM:
{(c.mecanique or "").strip()}

STRATEGIC ISSUE:
{(c.enjeu or "").strip()}

FRICTION:
{(c.friction or "").strip()}

NUMBERS:
{(c.chiffres or "").strip()}
"""

        blocks.append(
            block.strip()
        )

    return "\n\n====================\n\n".join(
        blocks
    )
