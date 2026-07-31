from core.digest.models import (
    DigestDocument,
)


# ============================================================
# DIGEST TYPE
# ============================================================

def build_digest_type(
    document: DigestDocument,
) -> str:
    """
    Build the digest type label.
    """

    frequency = document.frequency.upper()
    audience = document.audience.upper()

    return f"{frequency} {audience}"


# ============================================================
# HEADER
# ============================================================

def render_header(
    document: DigestDocument,
) -> str:
    """
    Render the digest header.
    """

    profile = document.profile

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

{build_digest_type(document)}

</div>

<h1>

Your Intelligence Briefing

</h1>

<p class="reader-name">

{profile.name}

</p>

<p class="reader-role">

{subtitle}

</p>

<p class="period">

{document.period}

</p>

</td>

</tr>
"""
