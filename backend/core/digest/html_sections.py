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

}


# ============================================================
# SECTIONS — FULL
# ============================================================

def render_sections(
    document: DigestDocument,
) -> str:
    """
    Render all digest sections.

    Used for:
    - email
    - admin preview
    """

    html = ""

    for section in document.sections:

        display_title = DISPLAY_TITLES.get(
            section.title,
            section.title,
        )

        # ====================================================
        # EXECUTIVE SUMMARY
        # ====================================================

        if section.title == "Executive Summary":

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
                section,
            )

        # ====================================================
        # KEY POINTS
        # ====================================================

        elif section.title == "Key Points":

            section.title = display_title

            html += render_key_points_section(
                section,
            )

        # ====================================================
        # STRATEGIC IMPLICATIONS
        # ====================================================

        elif section.title == "Strategic Implications":

            section.title = display_title

            html += render_implications_section(
                section,
            )

        # ====================================================
        # ARTICLES
        # ====================================================

        elif section.title == "Articles":

            section.title = display_title

            html += render_articles_section(
                section,
            )

        # ====================================================
        # DEFAULT
        # ====================================================

        else:

            section.title = display_title

            html += render_default_section(
                section,
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

    Same analytical output as the full Digest,
    but Supporting Articles are intentionally hidden.
    """

    html = ""

    for section in document.sections:

        # ====================================================
        # ARTICLES — NOT DISPLAYED ON FRONT
        # ====================================================

        if section.title == "Articles":
            continue

        display_title = DISPLAY_TITLES.get(
            section.title,
            section.title,
        )

        # ====================================================
        # EXECUTIVE SUMMARY
        # ====================================================

        if section.title == "Executive Summary":

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
                section,
            )

        # ====================================================
        # KEY POINTS
        # ====================================================

        elif section.title == "Key Points":

            section.title = display_title

            html += render_key_points_section(
                section,
            )

        # ====================================================
        # STRATEGIC IMPLICATIONS
        # ====================================================

        elif section.title == "Strategic Implications":

            section.title = display_title

            html += render_implications_section(
                section,
            )

        # ====================================================
        # DEFAULT
        # ====================================================

        else:

            section.title = display_title

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
