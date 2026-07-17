from api.expertise.models import ExpertiseContent


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
{c.title}

CONTENT:
{c.content_body}

SIGNAL:
{c.signal_analytique}

MECHANISM:
{c.mecanique_expliquee}

STRATEGIC ISSUE:
{c.enjeu_strategique}

FRICTION:
{c.point_de_friction}

NUMBERS:
{c.chiffres}
"""

        blocks.append(
            block.strip()
        )

    return "\n\n====================\n\n".join(
        blocks
    )
