# backend/core/digest/html_sections.py

from core.digest.models import (
    DigestBadge,
    DigestCard,
    DigestDocument,
    DigestSection,
)

from core.digest.html_badges import (
    render_badge,
)

from core.digest.html_summary import (
    render_summary_section,
)


# ============================================================
# SECTIONS
# ============================================================

def render_sections(
    document: DigestDocument,
) -> str:
    """
    Render all digest sections.
    """

    html = ""

    for section in document.sections:

        if section.title == "Executive Summary":

            html += render_summary_section(
                section,
            )

        elif section.title == "Key Points":

            html += render_key_points_section(
                section,
            )

        elif section.title == "Strategic Implications":

            html += render_implications_section(
                section,
            )

        elif section.title == "Articles":

            html += render_articles_section(
                section,
            )

        else:

            html += render_default_section(
                section,
            )

    return html

# ============================================================
# DEFAULT SECTION
# ============================================================

def render_default_section(
    section: DigestSection,
) -> str:
    """
    Default rendering for a digest section.
    """

    cards = "".join(
        render_card(card)
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
# KEY POINTS
# ============================================================

def render_key_points_section(
    section: DigestSection,
) -> str:

    return render_default_section(
        section,
    )


# ============================================================
# STRATEGIC IMPLICATIONS
# ============================================================

def render_implications_section(
    section: DigestSection,
) -> str:

    return render_default_section(
        section,
    )


# ============================================================
# ARTICLES
# ============================================================

def render_articles_section(
    section: DigestSection,
) -> str:

    return render_default_section(
        section,
    )

# ============================================================
# CARD
# ============================================================

def render_card(
    card: DigestCard,
) -> str:
    """
    Render a digest card.
    """

    meta = build_card_meta(
        card,
    )

    return f"""
<div class="card">

<h3>

{card.title}

</h3>

{render_card_badges(
    card.badges,
)}

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
# CARD META
# ============================================================

def build_card_meta(
    card: DigestCard,
) -> str:
    """
    Build the card metadata.
    """

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

    return meta


# ============================================================
# CARD BADGES
# ============================================================

def render_card_badges(
    badges: list[DigestBadge],
) -> str:
    """
    Render the badges attached to a card.
    """

    if not badges:

        return ""

    html = """
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
