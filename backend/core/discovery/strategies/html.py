# backend/core/discovery/strategies/html.py

from typing import (
    Dict,
    List,
)

from urllib.parse import (
    urlparse,
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
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


# ============================================================
# DISCOVER HTML
# ============================================================

def discover_html(
    source: dict,
) -> List[Dict]:

    page_url = source.get(
        "DOMAIN"
    )

    if not page_url:

        raise Exception(
            "DOMAIN manquant"
        )

    response = requests.get(
        page_url,
        headers=HEADERS,
        timeout=20,
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    page_domain = urlparse(
        page_url
    ).netloc.lower()

    results = []
    seen = set()

    for link in soup.find_all("a"):

        href = link.get(
            "href"
        )

        if not href:
            continue

        if not href.startswith(
            "http"
        ):
            continue

        href_domain = (
            urlparse(href)
            .netloc
            .lower()
        )

        if href_domain != page_domain:
            continue

        if "#" in href:
            continue

        href_lower = href.lower()

        excluded = [
            "/tag/",
            "/tags/",
            "/category/",
            "/categories/",
            "/author/",
            "/authors/",
            "/about",
            "/contact",
            "/privacy",
            "/terms",
            "/login",
            "/account",
        ]

        if any(
            x in href_lower
            for x in excluded
        ):
            continue

        title = (
            link.get_text(
                strip=True
            )
            or href
        )

        if href in seen:
            continue

        seen.add(
            href
        )

        results.append(
            {
                "url": href,
                "title": title,
            }
        )

    return results
