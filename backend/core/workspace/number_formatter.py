from typing import Any


# ============================================================
# NUMBER BLOCKS
# ============================================================

def build_number_blocks(
    numbers: list[dict[str, Any]],
) -> str:

    if not numbers:
        return "No numbers."

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
