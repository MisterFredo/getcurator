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

    return f"""
<tr>

<td class="summary">

<div class="summary-box">

<div class="summary-pill">

EXECUTIVE SUMMARY

</div>

<div class="summary-content">

{section.content}

</div>

</div>

</td>

</tr>
"""
