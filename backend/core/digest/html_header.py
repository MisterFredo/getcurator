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
    Render the digest cover.
    """

    profile = document.profile

    identity = profile.name

    details = []

    if profile.role:
        details.append(profile.role)

    if profile.company:
        details.append(profile.company)

    subtitle = " · ".join(details)

    return f"""
<tr>

<td class="header">

<div class="digest-type">

WEEKLY PERSONAL

</div>

<h1>

Your Intelligence Briefing

</h1>

<p class="reader-name">

{identity}

</p>

<p class="reader-role">

{subtitle}

</p>

<p class="period">

Week of {document.period}

</p>

<p class="prepared">

Prepared from your monitoring profile

</p>

</td>

</tr>
"""
