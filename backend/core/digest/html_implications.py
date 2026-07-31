# backend/core/digest/html_implications.py

from core.digest.models import (
    DigestSection,
)


# ============================================================
# STRATEGIC IMPLICATIONS
# ============================================================

def render_implications_section(
    section: DigestSection,
) -> str:
    """
    Render the Strategic Implications section.
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

        title = lines[0]

        body = "<br><br>".join(
            lines[1:]
        )

        html += f"""
<div class="market-card">

<h3>

{title}

</h3>

<p>

{body}

</p>

</div>
"""

    return f"""
<tr>

<td class="section implications">

<h2>

{section.title}

</h2>

<div class="implications-content">

{html}

</div>

</td>

</tr>
"""
