# backend/core/discovery/strategies/wordpress.py

from typing import (
    Dict,
    List,
)

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

}


# ============================================================
# NORMALIZE DOMAIN
# ============================================================

def normalize_domain(
    domain: str,
) -> str:

    domain = (
        domain
        .lower()
        .strip()
    )

    domain = domain.replace(
        "https://",
        "",
    )

    domain = domain.replace(
        "http://",
        "",
    )

    domain = domain.replace(
        "www.",
        "",
    )

    return domain.rstrip(
        "/"
    )


# ============================================================
# GET ENDPOINT
# ============================================================

def get_wordpress_endpoint(
    source: dict,
) -> str:

    domain = source.get(
        "DOMAIN"
    )

    if not domain:

        raise Exception(
            "DOMAIN manquant"
        )

    normalized_domain = (
        normalize_domain(
            domain
        )
    )

    endpoint = (
        SOURCE_ENDPOINTS.get(
            normalized_domain
        )
    )

    if endpoint:

        return endpoint

    # Standard WordPress fallback
    return (
        f"https://{normalized_domain}"
        "/wp-json/wp/v2/posts"
    )


# ============================================================
# DISCOVER WORDPRESS
# ============================================================

def discover_wordpress(
    source: dict,
) -> List[Dict]:

    endpoint = (
        get_wordpress_endpoint(
            source
        )
    )

    response = requests.get(
        endpoint,
        headers=HEADERS,
        params={
            "per_page": 100,
            "page": 1,
            "_fields": (
                "id,"
                "link,"
                "title,"
                "date"
            ),
        },
        timeout=30,
    )

    response.raise_for_status()

    posts = response.json()

    if not isinstance(
        posts,
        list,
    ):

        raise Exception(
            "Réponse WordPress invalide"
        )

    results = []

    for post in posts:

        url = post.get(
            "link"
        )

        if not url:
            continue

        title_data = (
            post.get(
                "title"
            )
            or {}
        )

        title = (
            title_data.get(
                "rendered"
            )
            or url
        )

        results.append(
            {
                "url": url,
                "title": title,
            }
        )

    return results
