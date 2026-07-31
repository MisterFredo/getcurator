# backend/core/digest/html_sections.py

from core.digest.models import (
    DigestCard,
    DigestDocument,
    DigestSection,
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

    return "".join(
        render_section(section)
        for section in document.sections
    )


# ============================================================
# SECTION
# ============================================================

def render_section(
    section: DigestSection,
) -> str:

    cards = ""

    if section.cards:

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
# CARD
# ============================================================

def render_card(
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
