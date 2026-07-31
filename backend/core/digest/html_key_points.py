# backend/core/digest/html_key_points.py

from core.digest.models import (
    DigestSection,
)

from core.digest.html_parser import (
    parse_market_developments,
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

    blocks = parse_market_developments(
        section.content,
    )

    html = ""

    for block in blocks:

        html += render_market_development(
            title=block["title"],
            summary=block["body"],
        )

    return f"""
<tr>

<td class="section key-points">

<h2>

{section.title}

</h2>

{html}

</td>

</tr>
"""


# ============================================================
# MARKET DEVELOPMENT
# ============================================================

def render_market_development(
    title: str,
    summary: str,
) -> str:
    """
    Render one market development.
    """

    return f"""
<div class="market-development">

<div class="market-development-title">

{title}

</div>

<div class="market-development-summary">

{summary}

</div>

</div>
"""
