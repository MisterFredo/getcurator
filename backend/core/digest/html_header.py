# backend/core/digest/html_header.py

from core.digest.models import (
    DigestDocument,
)


# ============================================================
# HEADER
# ============================================================

def render_header(
    document: DigestDocument,
) -> str:
    """
    Render the digest header.
    """

    subtitle = ""

    if document.subtitle:

        subtitle = f"""
<p class="subtitle">
    {document.subtitle}
</p>
"""

    return f"""
<tr>

<td class="header">

<h1>
    {document.title}
</h1>

{subtitle}

<p class="period">
    {document.period}
</p>

</td>

</tr>
"""
