# backend/core/digest/html_profile.py

from core.digest.models import (
    DigestBadge,
    DigestDocument,
    DigestProfile,
)


# ============================================================
# PROFILE
# ============================================================

def render_profile(
    document: DigestDocument,
) -> str:
    """
    Render the monitoring profile.
    """

    profile = document.profile

    return f"""
<tr>

<td class="profile">

<div class="profile-box">

<h2>

Monitoring Profile

</h2>

<p class="profile-intro">

Built from your saved monitoring preferences.

</p>

{render_profile_description(profile)}

{render_profile_badges(
    "Companies",
    profile.companies,
)}

{render_profile_badges(
    "Topics",
    profile.topics,
)}

{render_profile_badges(
    "Solutions",
    profile.solutions,
)}

{render_keywords(
    profile.keywords,
)}

</div>

</td>

</tr>
"""


# ============================================================
# PROFILE DESCRIPTION
# ============================================================

def render_profile_description(
    profile: DigestProfile,
) -> str:
    """
    Render the optional profile description.
    """

    if not profile.description:
        return ""

    return f"""
<p class="profile-description">

{profile.description}

</p>
"""


# ============================================================
# PROFILE BADGES
# ============================================================

def render_profile_badges(
    title: str,
    badges: list[DigestBadge],
) -> str:
    """
    Render a badge group from DigestBadge objects.
    """

    return render_badge_group(
        title=title,
        badges=badges,
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


# ============================================================
# KEYWORDS
# ============================================================

def render_keywords(
    keywords: list[str],
) -> str:
    """
    Render the keyword group.
    """

    badges = [

        DigestBadge(
            label=keyword,
            type="keyword",
        )

        for keyword in keywords

    ]

    return render_badge_group(
        title="Keywords",
        badges=badges,
    )
