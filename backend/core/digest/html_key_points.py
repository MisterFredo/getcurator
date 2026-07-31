# backend/core/digest/html_key_points.py

from core.digest.models import (
    DigestSection,
)


# ============================================================
# KEY POINTS
# ============================================================

def render_key_points_section(
    section: DigestSection,
) -> str:
    """
    Render the Key Points section.
    """

    html = ""

    blocks = [

        block.strip()

        for block in section.content.split(
            "--------------------------------------------------"
        )

        if block.strip()

    ]

    for block in blocks:

        lines = [

            line.strip()

            for line in block.splitlines()

            if line.strip()

        ]

        if not lines:

            continue

        body = "<br><br>".join(
            lines,
        )

        html += f"""
<div class="market-card">

<p>

{body}

</p>

</div>
"""

    return f"""
<tr>

<td class="section key-points">

<h2>

{section.title}

</h2>

<div class="key-points-content">

{html}

</div>

</td>

</tr>
"""
