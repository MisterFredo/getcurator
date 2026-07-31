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

    html = (
        section.content

        .replace(
            "MARKET DEVELOPMENT",
            '<div class="market-development-label">Market Development</div>',
        )

        .replace(
            "TITLE",
            '<div class="market-development-title-label">Title</div>',
        )

        .replace(
            "SUMMARY",
            '<div class="market-development-summary-label">Summary</div>',
        )

        .replace(
            "\n",
            "<br>",
        )
    )

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
