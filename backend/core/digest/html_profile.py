# backend/core/digest/html_profile.py

from core.digest.models import (
    DigestBadge,
    DigestDocument,
    DigestProfile,
)

from core.digest.html_badges import (
    render_badge_group,
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
    Render a profile badge group.
    """

    return render_badge_group(
        title=title,
        badges=badges,
    )


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
