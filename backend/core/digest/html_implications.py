from core.digest.models import (
    DigestSection,
)

from core.digest.html_parser import (
    parse_implications,
)


# ============================================================
# STRATEGIC IMPLICATIONS
# ============================================================

def render_implications_section(
    section: DigestSection,
) -> str:
    """
    Render the Strategic Implications section.
    """

    blocks = parse_implications(
        section.content,
    )

    html = "".join(

        render_implication(
            title=block["title"],
            analysis=block["body"],
        )

        for block in blocks

    )

    return f"""
<tr>

<td class="section implications">

<h2>

{section.title}

</h2>

{html}

</td>

</tr>
"""


# ============================================================
# IMPLICATION
# ============================================================

def render_implication(
    title: str,
    analysis: str,
) -> str:
    """
    Render one strategic implication.
    """

    return f"""
<div class="implication">

<div class="implication-title">

{title}

</div>

<div class="implication-analysis">

{analysis}

</div>

</div>
"""
