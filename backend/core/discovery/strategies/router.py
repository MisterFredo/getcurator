# backend/core/discovery/router.py

from typing import (
    Dict,
    List,
)

from core.discovery.strategies.html import (
    discover_html,
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
    # UNSUPPORTED
    # ========================================================

    raise Exception(
        f"Mode d'acquisition non supporté : {mode}"
    )
