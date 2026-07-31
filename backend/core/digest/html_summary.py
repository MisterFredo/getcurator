# backend/core/digest/html_summary.py

from core.digest.models import (
    DigestSection,
)


# ============================================================
# EXECUTIVE SUMMARY
# ============================================================

def render_summary_section(
    section: DigestSection,
) -> str:
    """
    Render the Executive Summary section.
    """

    content = (
        section.content
        .strip()
        .replace(
            "\n\n",
            "</p><p>",
        )
        .replace(
            "\n",
            " ",
        )
    )

    return f"""
<tr>

<td class="summary">

<div class="summary-box">

<div class="summary-pill">

EXECUTIVE SUMMARY

</div>

<div class="summary-content">

<p>{content}</p>

</div>

</div>

</td>

</tr>
"""
