# backend/core/digest/html_service.py

from core.digest.models import (
    DigestDocument,
)

from core.digest.html_head import (
    render_head,
)

from core.digest.html_header import (
    render_header,
)

from core.digest.html_profile import (
    render_profile,
)

from core.digest.html_sections import (
    render_sections,
)

from core.digest.html_footer import (
    render_footer,
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

{render_head()}

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

{render_header(document)}

{render_profile(document)}

{render_sections(document)}

{render_footer()}

</table>

</td>

</tr>

</table>

</body>

</html>
"""
