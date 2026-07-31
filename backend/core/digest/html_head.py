# backend/core/digest/html_head.py

from core.digest.html_styles import (
    DIGEST_EMAIL_STYLES,
)


# ============================================================
# HEAD
# ============================================================

def render_head() -> str:
    """
    Render the HTML <head>.
    """

    return f"""
<head>

<meta charset="utf-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0">

<title>
    GetCurator Digest
</title>

<style>

{DIGEST_EMAIL_STYLES}

</style>

</head>
"""
