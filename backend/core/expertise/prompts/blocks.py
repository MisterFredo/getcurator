from api.expertise.models import (
    ExpertiseContent,
)


# ============================================================
# CONTENT BLOCKS
# ============================================================

def build_content_blocks(
    contents: list[ExpertiseContent],
) -> str:

    if not contents:
        return "No content."

    blocks = []

    for c in contents:

        block = f"""
TITLE:
{(c.title or "").strip()}

CONTENT:
{(c.content_body or "").strip()}

SIGNAL:
{(c.signal_analytique or "").strip()}

MECHANISM:
{(c.mecanique_expliquee or "").strip()}

STRATEGIC ISSUE:
{(c.enjeu_strategique or "").strip()}

FRICTION:
{(c.point_de_friction or "").strip()}

NUMBERS:
{(c.chiffres or "").strip()}
"""

        blocks.append(
            block.strip()
        )

    return "\n\n====================\n\n".join(
        blocks
    )
