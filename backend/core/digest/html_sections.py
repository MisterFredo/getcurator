from core.digest.models import (
    DigestDocument,
    DigestSection,
)

from core.digest.html_summary import (
    render_summary_section,
)

from core.digest.html_key_points import (
    render_key_points_section,
)

from core.digest.html_implications import (
    render_implications_section,
)

from core.digest.html_articles import (
    render_articles_section,
)


# ============================================================
# DISPLAY TITLES
# ============================================================

DISPLAY_TITLES = {

    "Executive Summary":
        "Your Executive Brief",

    "Key Points":
        "Market Developments",

    "Strategic Implications":
        "What This Means for You",

    "Articles":
        "Supporting Articles",

    "Must Read":
        "Must Read",

    "Also Worth Your Attention":
        "Also Worth Your Attention",

}


# ============================================================
# DISPLAY SECTION
# ============================================================

def _build_display_section(
    section: DigestSection,
    display_title: str,
) -> DigestSection:

    return section.model_copy(

        update={
            "title":
                display_title,
        },

    )


# ============================================================
# SECTIONS — FULL
# ============================================================

def render_sections(
    document: DigestDocument,
) -> str:
    """
    Render all Digest sections.

    Used for:
    - email;
    - admin preview;
    - manual copy and paste.
    """

    html = ""

    for section in document.sections:

        display_title = DISPLAY_TITLES.get(
            section.title,
            section.title,
        )

        display_section = (
            _build_display_section(
                section=section,
                display_title=display_title,
            )
        )

        # ====================================================
        # EXECUTIVE SUMMARY
        # ====================================================

        if (
            section.title
            == "Executive Summary"
        ):

            html += f"""
<tr>

<td class="section">

<h2>

{display_title}

</h2>

</td>

</tr>
"""

            html += render_summary_section(
                display_section,
            )

        # ====================================================
        # KEY POINTS
        # ====================================================

        elif (
            section.title
            == "Key Points"
        ):

            html += render_key_points_section(
                display_section,
            )

        # ====================================================
        # STRATEGIC IMPLICATIONS
        # ====================================================

        elif (
            section.title
            == "Strategic Implications"
        ):

            html += (
                render_implications_section(
                    display_section
                )
            )

        # ====================================================
        # ARTICLE SECTIONS
        # ====================================================

        elif section.cards:

            html += render_articles_section(
                display_section,
            )

        # ====================================================
        # DEFAULT
        # ====================================================

        else:

            html += render_default_section(
                display_section,
            )

    return html


# ============================================================
# SECTIONS — FRONT
# ============================================================

def render_front_sections(
    document: DigestDocument,
) -> str:
    """
    Render Digest sections for the public front.

    Article cards remain intentionally hidden
    from this reduced rendering.
    """

    html = ""

    for section in document.sections:

        # ====================================================
        # ARTICLE CARDS — NOT DISPLAYED ON REDUCED FRONT
        # ====================================================

        if section.cards:

            continue

        display_title = DISPLAY_TITLES.get(
            section.title,
            section.title,
        )

        display_section = (
            _build_display_section(
                section=section,
                display_title=display_title,
            )
        )

        # ====================================================
        # EXECUTIVE SUMMARY
        # ====================================================

        if (
            section.title
            == "Executive Summary"
        ):

            html += f"""
<tr>

<td class="section">

<h2>

{display_title}

</h2>

</td>

</tr>
"""

            html += render_summary_section(
                display_section,
            )

        # ====================================================
        # KEY POINTS
        # ====================================================

        elif (
            section.title
            == "Key Points"
        ):

            html += render_key_points_section(
                display_section,
            )

        # ====================================================
        # STRATEGIC IMPLICATIONS
        # ====================================================

        elif (
            section.title
            == "Strategic Implications"
        ):

            html += (
                render_implications_section(
                    display_section
                )
            )

        # ====================================================
        # DEFAULT
        # ====================================================

        else:

            html += render_default_section(
                display_section,
            )

    return html


# ============================================================
# DEFAULT SECTION
# ============================================================

def render_default_section(
    section: DigestSection,
) -> str:
    """
    Default rendering for a Digest section.
    """

    return f"""
<tr>

<td class="section">

<h2>

{section.title}

</h2>

<div class="section-content">

{section.content}

</div>

</td>

</tr>
"""
