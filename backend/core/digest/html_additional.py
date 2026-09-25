from html import escape

from core.digest.models import (
    DigestCard,
    DigestDocument,
)

from core.digest.html_articles import (
    build_card_meta,
)


# ============================================================
# CONFIGURATION
# ============================================================

ADDITIONAL_SECTION_TITLE = (
    "Also on Your Radar"
)

ADDITIONAL_SECTION_DESCRIPTION = (
    "Additional signals identified during "
    "this week’s review."
)


# ============================================================
# ADDITIONAL CONTENTS
# ============================================================

def render_additional_contents(
    document: DigestDocument,
) -> str:
    """
    Render lightweight additional content links.

    These contents are not part of the analytical foundation
    used for the Executive Brief or Strategic Implications.
    """

    if not document.additional_contents:

        return ""

    cards = "".join(

        render_additional_card(
            card
        )

        for card in (
            document.additional_contents
        )

    )

    return f"""
<tr>

<td class="section articles additional-contents">

<h2>

{ADDITIONAL_SECTION_TITLE}

</h2>

<p class="section-content">

{ADDITIONAL_SECTION_DESCRIPTION}

</p>

{cards}

</td>

</tr>
"""


# ============================================================
# ADDITIONAL CARD
# ============================================================

def render_additional_card(
    card: DigestCard,
) -> str:
    """
    Render one lightweight additional signal.

    No full excerpt, badges or generated implication are shown.
    """

    title = escape(
        card.title
        or ""
    )

    url = escape(
        card.url
        or "",
        quote=True,
    )

    meta = escape(
        build_card_meta(
            card
        )
    )

    reason = escape(
        card.selection_reason
        or ""
    )

    meta_html = (

        f"""
<p class="meta">

{meta}

</p>
"""

        if meta

        else ""

    )

    reason_html = (

        f"""
<p>

{reason}

</p>
"""

        if reason

        else ""

    )

    return f"""
<div class="card additional-card">

<h3>

<a
    href="{url}"
    target="_blank"
    rel="noopener noreferrer"
>

{title}

</a>

</h3>

{meta_html}

{reason_html}

<p>

<a
    href="{url}"
    class="cta"
    target="_blank"
    rel="noopener noreferrer"
>

Read on GetCurator →

</a>

</p>

</div>
"""
