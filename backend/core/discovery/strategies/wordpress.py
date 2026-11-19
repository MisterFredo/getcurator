
# backend/core/discovery/strategies/wordpress.py

from typing import Dict, List
from urllib.parse import urlparse
from html import unescape

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
    ),
    "Accept": "application/json",
}


# ============================================================
# SOURCE ENDPOINTS
# ============================================================

SOURCE_ENDPOINTS = {
    "retailnews.asia":
        "https://crm.retailnews.asia/wp-json/wp/v2/posts",

    "broadbandtvnews.com":
        "https://www.broadbandtvnews.com/wp-json/wp/v2/posts",
}


# ============================================================
# NORMALIZE DOMAIN
# ============================================================

def normalize_domain(domain: str) -> str:

    domain = domain.lower().strip()

    if not domain.startswith(("http://", "https://")):
        domain = f"https://{domain}"

    parsed = urlparse(domain)

    hostname = (parsed.hostname or "").lower()

    if hostname.startswith("www."):
        hostname = hostname[4:]

    return hostname


# ============================================================
# GET ENDPOINT
# ============================================================

def get_wordpress_endpoint(source: dict) -> str:

    domain = source.get("DOMAIN")

    if not domain:
        raise Exception("DOMAIN manquant")

    normalized_domain = normalize_domain(domain)

    if not normalized_domain:
        raise Exception("DOMAIN invalide")

    endpoint = SOURCE_ENDPOINTS.get(normalized_domain)

    if endpoint:
        return endpoint

    return (
        f"https://{normalized_domain}"
        "/wp-json/wp/v2/posts"
    )


# ============================================================
# DISCOVER WORDPRESS
# ============================================================

def discover_wordpress(source: dict) -> List[Dict]:

    endpoint = get_wordpress_endpoint(source)

    print(
        f"[DISCOVERY WP] ENDPOINT={endpoint}"
    )

    # ========================================================
    # FETCH API
    # ========================================================

    try:
        response = requests.get(
            endpoint,
            headers=HEADERS,
            params={
                "per_page": 100,
                "page": 1,
                "_fields": "id,link,title,date",
            },
            timeout=30,
            allow_redirects=True,
        )

    except requests.RequestException as exc:
        raise Exception(
            f"WordPress API : erreur réseau "
            f"pour {endpoint} : {exc}"
        ) from exc

    # ========================================================
    # HTTP DIAGNOSTICS
    # ========================================================

    content_type = response.headers.get(
        "Content-Type", ""
    ).lower()

    print(
        f"[DISCOVERY WP] STATUS={response.status_code}"
    )

    print(
        f"[DISCOVERY WP] FINAL_URL={response.url}"
    )

    print(
        f"[DISCOVERY WP] CONTENT_TYPE={content_type}"
    )

    print(
        f"[DISCOVERY WP] REDIRECTS={len(response.history)}"
    )

    # ========================================================
    # DETECT ANTI-BOT PROTECTION
    # ========================================================

    preview = response.text[:5000].lower()

    protection_signatures = (
        "sucuri_cloudproxy",
        "cloudflare challenge",
        "cf-chl-",
        "javascript is required",
        "enable javascript before you are allowed",
    )

    if any(
        signature in preview
        for signature in protection_signatures
    ):
        raise Exception(
            "WordPress API : accès bloqué par une "
            f"protection anti-bot pour {endpoint}"
        )

    # ========================================================
    # VALIDATE HTTP STATUS
    # ========================================================

    if response.status_code != 200:
        raise Exception(
            f"WordPress API : HTTP {response.status_code} "
            f"pour {endpoint}"
        )

    # ========================================================
    # VALIDATE CONTENT TYPE
    # ========================================================

    if (
        "application/json" not in content_type
        and "+json" not in content_type
    ):
        raise Exception(
            "WordPress API : réponse non JSON "
            f"({content_type}) pour {endpoint}"
        )

    # ========================================================
    # PARSE JSON
    # ========================================================

    try:
        posts = response.json()

    except ValueError as exc:
        raise Exception(
            f"WordPress API : JSON invalide "
            f"pour {endpoint}"
        ) from exc

    if not isinstance(posts, list):
        raise Exception(
            "WordPress API : réponse invalide, "
            "une liste d'articles était attendue"
        )

    print(
        f"[DISCOVERY WP] POSTS={len(posts)}"
    )

    # ========================================================
    # EXTRACT POSTS
    # ========================================================

    results = []
    seen = set()

    for post in posts:

        if not isinstance(post, dict):
            continue

        url = post.get("link")

        if not isinstance(url, str) or not url.strip():
            continue

        url = url.strip()

        if url in seen:
            continue

        seen.add(url)

        title_data = post.get("title") or {}

        if isinstance(title_data, dict):
            title = title_data.get("rendered") or url
        elif isinstance(title_data, str):
            title = title_data
        else:
            title = url

        # Remove HTML tags and decode entities
        title = BeautifulSoup(
            unescape(title),
            "html.parser",
        ).get_text(" ", strip=True) or url

        results.append(
            {
                "url": url,
                "title": title,
            }
        )

    print(
        f"[DISCOVERY WP] RESULTS={len(results)}"
    )

    return results
