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

        value = " ".join(

            part

            for part in (

                str(n.get("value") or "").strip(),

                str(n.get("unit") or "").strip(),

                str(n.get("scale") or "").strip(),

            )

            if part

        )

        block = f"""
LABEL:
{str(n.get("label") or "").strip()}

VALUE:
{value}

TYPE:
{str(n.get("type") or "").strip()}

CATEGORY:
{str(n.get("category") or "").strip()}

ZONE:
{str(n.get("zone") or "").strip()}

PERIOD:
{str(n.get("period") or "").strip()}

ENTITY:
{str(n.get("entity_label") or "").strip()}
"""

        blocks.append(
            block.strip()
        )

    return "\n\n--------------------\n\n".join(
        blocks
    )
