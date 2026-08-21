# backend/core/discovery/strategies/rss.py

from typing import (
    Dict,
    List,
)

import xml.etree.ElementTree as ET

import requests


# ============================================================
# HTTP
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/150.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "application/rss+xml,"
        "application/xml,"
        "text/xml,"
        "*/*"
    ),
}


# ============================================================
# DISCOVER RSS
# ============================================================

def discover_rss(
    source: dict,
) -> List[Dict]:

    feed_url = source.get(
        "DOMAIN"
    )

    if not feed_url:

        raise Exception(
            "DOMAIN manquant"
        )

    # ========================================================
    # FETCH RSS
    # ========================================================

    response = requests.get(
        feed_url,
        headers=HEADERS,
        timeout=30,
    )

    response.raise_for_status()

    # ========================================================
    # PARSE XML
    # ========================================================

    try:

        root = ET.fromstring(
            response.content
        )

    except ET.ParseError as e:

        raise Exception(
            f"RSS XML invalide : {e}"
        )

    # ========================================================
    # EXTRACT ITEMS
    # ========================================================

    results = []
    seen = set()

    for item in root.findall(
        ".//item"
    ):

        # ====================================================
        # URL
        # ====================================================

        link_element = item.find(
            "link"
        )

        if link_element is None:
            continue

        url = (
            link_element.text
            or ""
        ).strip()

        if not url:
            continue

        # ====================================================
        # DEDUPLICATION
        # ====================================================

        if url in seen:
            continue

        seen.add(
            url
        )

        # ====================================================
        # TITLE
        # ====================================================

        title_element = item.find(
            "title"
        )

        title = url

        if (
            title_element is not None
            and title_element.text
        ):

            title = (
                title_element.text
            ).strip()

        # ====================================================
        # RESULT
        # ====================================================

        results.append(
            {
                "url": url,
                "title": title,
            }
        )

    return results
