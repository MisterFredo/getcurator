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

    profile = document.profile

    return f"""
<tr>

<td class="profile">

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

</td>

</tr>
"""

# ============================================================
# PROFILE DESCRIPTION
# ============================================================

def render_profile_description(
    profile: DigestProfile,
) -> str:

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

def render_profile(
    document: DigestDocument,
) -> str:
    """
    Render the monitoring profile.
    """

    return render_badge_group(
        title,
        [badge.label for badge in badges],
    )

# ============================================================
# BADGE GROUP
# ============================================================

def render_badge_group(
    title: str,
    labels: list[str],
) -> str:
    """
    Render a titled group of badges.
    """

    if not labels:
        return ""

    html = f"""
<h3>

{title}

</h3>

<div class="badge-list">
"""

    for label in labels:

        html += f"""
<span class="badge">

{label}

</span>
"""

    html += """
</div>
"""

    return html

# ============================================================
# KEYWORDS
# ============================================================

def render_keywords(
    keywords: list[str],
) -> str:

    return render_badge_group(
        "Keywords",
        keywords,
    )
