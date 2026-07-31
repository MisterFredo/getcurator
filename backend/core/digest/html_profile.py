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

<h2>

Your Monitoring Profile

</h2>

{render_profile_identity(profile)}

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
# PROFILE IDENTITY
# ============================================================

def render_profile_identity(
    profile: DigestProfile,
) -> str:

    subtitle = []

    if profile.role:
        subtitle.append(profile.role)

    if profile.company:
        subtitle.append(profile.company)

    html = f"""
<p>

<strong>{profile.name}</strong>

</p>
"""

    if subtitle:

        html += f"""
<p>

{" · ".join(subtitle)}

</p>
"""

    if profile.description:

        html += f"""
<p class="profile-description">

{profile.description}

</p>
"""

    return html


# ============================================================
# PROFILE BADGES
# ============================================================

def render_profile_badges(
    title: str,
    badges: list[DigestBadge],
) -> str:

    if not badges:

        return ""

    html = f"""
<h3>

{title}

</h3>

<div class="badge-list">
"""

    for badge in badges:

        html += f"""
<span class="badge">

{badge.label}

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

    if not keywords:

        return ""

    html = """
<h3>

Keywords

</h3>

<div class="badge-list">
"""

    for keyword in keywords:

        html += f"""
<span class="badge">

{keyword}

</span>
"""

    html += """
</div>
"""

    return html
