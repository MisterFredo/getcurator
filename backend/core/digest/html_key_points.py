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

    return f"""
<tr>

<td class="section key-points">

<h2>

{section.title}

</h2>

<div class="key-points-content">

{section.content}

</div>

</td>

</tr>
"""
