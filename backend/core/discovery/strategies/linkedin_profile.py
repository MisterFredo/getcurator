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
# TEST LINKEDIN PROFILE
# ============================================================

def test_linkedin_profile(
    profile_url: str,
):

    # ========================================================
    # EXTRACT SLUG
    # ========================================================

    parsed = urlparse(
        profile_url
    )

    parts = [
        part
        for part in parsed.path.split("/")
        if part
    ]

    if len(parts) < 2 or parts[0] != "in":

        raise Exception(
            "URL profil LinkedIn invalide"
        )

    slug = parts[1]

    canonical_url = (
        f"https://www.linkedin.com/in/{slug}"
    )

    print(
        f"[LINKEDIN TEST] PROFILE={canonical_url}"
    )

    print(
        f"[LINKEDIN TEST] SLUG={slug}"
    )

    # ========================================================
    # FETCH
    # ========================================================

    session = requests.Session()

    response = session.get(
        canonical_url,
        headers=HEADERS,
        timeout=20,
        allow_redirects=True,
    )

    print(
        f"[LINKEDIN TEST] STATUS={response.status_code}"
    )

    print(
        f"[LINKEDIN TEST] FINAL_URL={response.url}"
    )

    print(
        f"[LINKEDIN TEST] HTML_SIZE={len(response.text)}"
    )

    # ========================================================
    # HTML ANALYSIS
    # ========================================================

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    links = soup.find_all(
        "a",
        href=True,
    )

    print(
        f"[LINKEDIN TEST] LINKS={len(links)}"
    )

    # ========================================================
    # DETECT LOGIN / AUTH WALL
    # ========================================================

    html_lower = (
        response.text.lower()
    )

    login_signals = [
        "authwall",
        "sign in",
        "join linkedin",
        "login",
    ]

    detected_signals = [
        signal
        for signal in login_signals
        if signal in html_lower
    ]

    print(
        "[LINKEDIN TEST] "
        f"LOGIN_SIGNALS={detected_signals}"
    )

    # ========================================================
    # FIND POSTS BELONGING TO SLUG
    # ========================================================

    post_marker = (
        f"/posts/{slug}_"
    )

    posts = []

    seen = set()

    for link in links:

        href = (
            link.get("href")
            or ""
        ).strip()

        if not href:
            continue

        if post_marker not in href:
            continue

        if href in seen:
            continue

        seen.add(
            href
        )

        title = link.get_text(
            " ",
            strip=True,
        )

        posts.append(
            {
                "url": href,
                "title": title,
            }
        )

    print(
        f"[LINKEDIN TEST] POSTS={len(posts)}"
    )

    for post in posts[:20]:

        print(
            "[LINKEDIN TEST] "
            f"POST={post['url']}"
        )

    # ========================================================
    # RESULT
    # ========================================================

    return {
        "status_code": response.status_code,
        "final_url": response.url,
        "html_size": len(response.text),
        "links": len(links),
        "login_signals": detected_signals,
        "slug": slug,
        "posts_found": len(posts),
        "posts": posts[:20],
    }
