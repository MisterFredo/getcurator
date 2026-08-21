# backend/core/discovery/router.py

from typing import (
    Dict,
    List,
)

from core.discovery.strategies.html import (
    discover_html,
)

from core.discovery.strategies.wordpress import (
    discover_wordpress,
)

from core.discovery.strategies.rss import (
    discover_rss,
)


# ============================================================
# DISCOVERY ROUTER
# ============================================================

def discover_urls(
    source: dict,
) -> List[Dict]:

    mode = (
        source.get(
            "ACQUISITION_MODE"
        )
        or ""
    ).upper()


    # ========================================================
    # MANUAL
    # ========================================================

    if mode == "MANUAL":

        return []


    # ========================================================
    # HTML
    # ========================================================

    if mode == "HTML":

        return discover_html(
            source
        )


    # ========================================================
    # WORDPRESS API
    # ========================================================

    if mode == "WORDPRESS_API":

        return discover_wordpress(
            source
        )


    # ========================================================
    # RSS
    # ========================================================

    if mode == "RSS":

        return discover_rss(
            source
        )


    # ========================================================
    # UNSUPPORTED
    # ========================================================

    raise Exception(
        f"Mode d'acquisition non supporté : {mode}"
    )
