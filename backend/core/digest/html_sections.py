# backend/core/digest/html_sections.py

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
