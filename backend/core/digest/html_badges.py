# backend/core/digest/html_badges.py

from core.digest.models import (
    DigestBadge,
)


# ============================================================
# BADGE GROUP
# ============================================================

def render_badge_group(
    title: str,
    badges: list[DigestBadge],
) -> str:
    """
    Render a titled group of badges.
    """

    if not badges:
        return ""

    html = f"""
<h3>

{title}

</h3>

<div class="badge-list">
"""

    for badge in badges:

        html += render_badge(
            badge,
        )

    html += """
</div>
"""

    return html


# ============================================================
# BADGE
# ============================================================

def render_badge(
    badge: DigestBadge,
) -> str:
    """
    Render a single badge.
    """

    return f"""
<span class="badge badge-{badge.type}">

{badge.label}

</span>
"""
