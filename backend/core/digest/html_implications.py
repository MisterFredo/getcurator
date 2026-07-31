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

    html = (
        section.content

        .replace(
            "STRATEGIC IMPLICATION",
            '<div class="strategic-implication-label">Strategic Implication</div>',
        )

        .replace(
            "TITLE",
            '<div class="strategic-implication-title-label">Title</div>',
        )

        .replace(
            "ANALYSIS",
            '<div class="strategic-implication-analysis-label">Analysis</div>',
        )

        .replace(
            "\n",
            "<br>",
        )
    )

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
