# backend/core/digest/html_header.py

from core.digest.models import (
    DigestDocument,
)


# ============================================================
# DIGEST TYPE
# ============================================================

def build_digest_type(
    document,
) -> str:
    """
    Build the visible Digest type.
    """

    return (
        f"WEEKLY "
        f"{document.audience.upper()} "
        f"DIGEST"
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

    return f"""
<tr>

<td class="header">

<h1>

Your Intelligence Briefing

<span class="by-getcurator">

by GetCurator

</span>

</h1>

<p class="digest-meta">

{build_digest_type(document)} · {document.period}

</p>

</td>

</tr>
"""
