from core.digest.models import (
    DigestBadge,
    DigestCard,
    DigestSection,
)

from core.digest.html_badges import (
    render_badge,
)


# ============================================================
# ARTICLES
# ============================================================

def render_articles_section(
    section: DigestSection,
) -> str:
    """
    Render the related articles section.
    """

    cards = "".join(
        render_card(card)
        for card in section.cards
    )

    return f"""
<tr>

<td class="section articles">

<h2>

{section.title}

</h2>

{cards}

</td>

</tr>
"""


# ============================================================
# CARD
# ============================================================

def render_card(
    card: DigestCard,
) -> str:
    """
    Render an article card.
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
    class="cta"
    target="_blank"
    rel="noopener noreferrer">

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
    Build the article metadata.
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
    Render the badges attached to an article.
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
