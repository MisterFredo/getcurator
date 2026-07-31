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

    return f"""
<tr>

<td class="section implications">

<h2>

{section.title}

</h2>

<div class="section-content">

{section.content}

</div>

</td>

</tr>
"""
