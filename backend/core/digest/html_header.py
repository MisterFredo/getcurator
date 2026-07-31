# backend/core/digest/html_header.py

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

    return (
        f"{document.frequency.upper()} "
        f"{document.audience.upper()}"
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

    profile = document.profile

    company = (
        f" · {profile.company}"
        if profile.company
        else ""
    )

    return f"""
<tr>

<td class="header">

<p class="digest-meta">

{build_digest_type(document)} · {document.period}

</p>

<p class="reader-name">

{profile.name}{company}

</p>

<h1>

Your Intelligence Briefing

</h1>

</td>

</tr>
"""
