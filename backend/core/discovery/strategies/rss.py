# backend/core/discovery/strategies/rss.py

from typing import (
    Dict,
    List,
)

import requests

from bs4 import BeautifulSoup


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

    soup = BeautifulSoup(
        response.content,
        "xml",
    )

    results = []
    seen = set()

    # ========================================================
    # RSS ITEMS
    # ========================================================

    for item in soup.find_all(
        "item"
    ):

        link = item.find(
            "link"
        )

        if not link:
            continue

        url = link.get_text(
            strip=True
        )

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

        title_tag = item.find(
            "title"
        )

        title = (
            title_tag.get_text(
                strip=True
            )
            if title_tag
            else url
        )

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
