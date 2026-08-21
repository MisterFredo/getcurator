# backend/core/discovery/strategies/html.py

from typing import (
    Dict,
    List,
)

from urllib.parse import (
    urljoin,
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
        "Chrome/150.0.0.0 Safari/537.36"
    ),

    "Accept": (
        "text/html,"
        "application/xhtml+xml,"
        "application/xml;q=0.9,"
        "image/avif,"
        "image/webp,"
        "*/*;q=0.8"
    ),

    "Accept-Language": (
        "en-GB,en;q=0.9"
    ),

    "Cache-Control": (
        "no-cache"
    ),

    "Pragma": (
        "no-cache"
    ),

    "Upgrade-Insecure-Requests": (
        "1"
    ),

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


    # ========================================================
    # FETCH PAGE
    # ========================================================

    session = requests.Session()

    response = session.get(
        page_url,
        headers=HEADERS,
        timeout=20,
        allow_redirects=True,
    )

    response.raise_for_status()


    # ========================================================
    # PARSE HTML
    # ========================================================

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )


    # ========================================================
    # DEBUG
    # ========================================================

    print(
        f"[DISCOVERY HTML] URL={page_url}"
    )

    print(
        f"[DISCOVERY HTML] STATUS={response.status_code}"
    )

    print(
        f"[DISCOVERY HTML] FINAL_URL={response.url}"
    )

    print(
        f"[DISCOVERY HTML] HTML_SIZE={len(response.text)}"
    )

    print(
        f"[DISCOVERY HTML] LINKS={len(soup.find_all('a'))}"
    )


    # ========================================================
    # PAGE DOMAIN
    # ========================================================

    page_domain = (
        urlparse(
            page_url
        )
        .netloc
        .lower()
    )

    results = []
    seen = set()


    # ========================================================
    # EXTRACT LINKS
    # ========================================================

    for link in soup.find_all(
        "a"
    ):

        href = link.get(
            "href"
        )

        if not href:
            continue

        href = href.strip()

        if not href:
            continue


        # ====================================================
        # DEBUG RAW HREF
        # ====================================================

        print(
            f"[DISCOVERY HTML] HREF={href}"
        )


        # ====================================================
        # IGNORE NON-WEB LINKS
        # ====================================================

        if href.startswith(
            (
                "mailto:",
                "tel:",
                "javascript:",
            )
        ):
            continue


        # ====================================================
        # RELATIVE → ABSOLUTE URL
        # ====================================================

        href = urljoin(
            page_url,
            href,
        )


        # ====================================================
        # DOMAIN FILTER
        # ====================================================

        href_domain = (
            urlparse(
                href
            )
            .netloc
            .lower()
        )

        if (
            href_domain !=
            page_domain
        ):
            continue


        # ====================================================
        # IGNORE ANCHORS
        # ====================================================

        if "#" in href:
            continue


        # ====================================================
        # EXCLUDED PATHS
        # ====================================================

        href_lower = (
            href.lower()
        )

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
            excluded_path in href_lower
            for excluded_path in excluded
        ):
            continue


        # ====================================================
        # TITLE
        # ====================================================

        title = (
            link.get_text(
                strip=True
            )
            or href
        )


        # ====================================================
        # DEDUPLICATION
        # ====================================================

        if href in seen:
            continue

        seen.add(
            href
        )


        # ====================================================
        # RESULT
        # ====================================================

        results.append(
            {
                "url": href,
                "title": title,
            }
        )


    # ========================================================
    # DEBUG RESULT
    # ========================================================

    print(
        f"[DISCOVERY HTML] RESULTS={len(results)}"
    )


    # ========================================================
    # RETURN
    # ========================================================

    return results
