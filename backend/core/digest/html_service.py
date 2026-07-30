# backend/core/digest/html_service.py

from core.digest.models import (
    DigestBadge,
    DigestCard,
    DigestDocument,
    DigestProfile,
    DigestSection,
)

from core.digest.html_styles import (
    DIGEST_EMAIL_STYLES,
)


# ============================================================
# PUBLIC
# ============================================================

def render_digest_html(
    document: DigestDocument,
) -> str:
    """
    Render a DigestDocument into an HTML email.
    """

    return f"""
<!DOCTYPE html>

<html>

{_render_head()}

<body>

<table
    width="100%"
    cellpadding="0"
    cellspacing="0">

<tr>

<td align="center">

<table
    width="700"
    cellpadding="0"
    cellspacing="0">

{_render_header(document)}

{_render_profile(document)}

{_render_sections(document)}

{_render_footer()}

</table>

</td>

</tr>

</table>

</body>

</html>
"""


# ============================================================
# HEAD
# ============================================================

def _render_head() -> str:

    return f"""
<head>

<meta charset="utf-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0">

<title>GetCurator Digest</title>

<style>

{DIGEST_EMAIL_STYLES}

</style>

</head>
"""


# ============================================================
# HEADER
# ============================================================

def _render_header(
    document: DigestDocument,
) -> str:

    subtitle = ""

    if document.subtitle:

        subtitle = f"""
<p class="subtitle">
    {document.subtitle}
</p>
"""

    return f"""
<tr>

<td class="header">

<h1>
    {document.title}
</h1>

{subtitle}

<p class="period">
    {document.period}
</p>

</td>

</tr>
"""

# ============================================================
# PROFILE
# ============================================================

def _render_profile(
    document: DigestDocument,
) -> str:

    profile = document.profile

    return f"""
<tr>

<td class="profile">

<h2>

Your Monitoring Profile

</h2>

{_render_profile_identity(profile)}

{_render_profile_badges(
    "Companies",
    profile.companies,
)}

{_render_profile_badges(
    "Topics",
    profile.topics,
)}

{_render_profile_badges(
    "Solutions",
    profile.solutions,
)}

{_render_keywords(
    profile.keywords,
)}

</td>

</tr>
"""

# ============================================================
# PROFILE IDENTITY
# ============================================================

def _render_profile_identity(
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
# SECTIONS
# ============================================================

def _render_sections(
    document: DigestDocument,
) -> str:

    return "".join(
        _render_section(section)
        for section in document.sections
    )

# ============================================================
# BADGES
# ============================================================

def _render_profile_badges(
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

def _render_keywords(
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


# ============================================================
# SECTION
# ============================================================

def _render_section(
    section: DigestSection,
) -> str:

    cards = ""

    if section.cards:

        cards = "".join(
            _render_card(card)
            for card in section.cards
        )

    return f"""
<tr>

<td class="section">

<h2>
    {section.title}
</h2>

<div class="section-content">

{section.content}

</div>

{cards}

</td>

</tr>
"""


# ============================================================
# CARD
# ============================================================

def _render_card(
    card: DigestCard,
) -> str:

    meta = ""

    if card.source_title:

        meta = card.source_title

    if card.published_at:

        date = card.published_at.strftime(
            "%d %b %Y"
        )

        if meta:

            meta += f" • {date}"

        else:

            meta = date

    return f"""
<div class="card">

<h3>

{card.title}

</h3>

<p class="meta">

{meta}

</p>

<p>

{card.excerpt}

</p>

<p>

<a
    href="{card.url}"
    class="cta">

Read on GetCurator →

</a>

</p>

</div>
"""


# ============================================================
# FOOTER
# ============================================================

def _render_footer() -> str:

    return """
<tr>

<td class="footer">

Powered by GetCurator

</td>

</tr>
"""
