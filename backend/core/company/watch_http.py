"""Dedicated HTML acquisition. Never calls the media Discovery service."""
from __future__ import annotations

import ipaddress
import json
import re
import socket
from urllib.parse import urljoin, urlsplit, urlunsplit, parse_qsl, urlencode

import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date

MAX_BYTES = 5 * 1024 * 1024
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CuratorCompanyWatch/1.0)",
           "Accept": "text/html,application/xhtml+xml", "Accept-Language": "fr,en;q=0.8"}


def normalize_url(value: str) -> str:
    parts = urlsplit(value.strip())
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
        raise ValueError("URL HTTP(S) absolue requise")
    if parts.username or parts.password or parts.port not in {None, 80, 443}:
        raise ValueError("Identifiants ou port non pris en charge")
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path or "/", parts.query, ""))


def url_key(value: str) -> str:
    """Comparison key only: keep the original URL for fetching and provenance."""
    parts = urlsplit(normalize_url(value))
    query = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True)
             if not key.lower().startswith("utm_") and key.lower() not in {
                 "fbclid", "gclid", "msclkid", "li_fat_id", "mc_cid", "mc_eid"}]
    host = parts.hostname
    if ":" in host:
        host = f"[{host}]"
    if parts.port and parts.port != (443 if parts.scheme == "https" else 80):
        host += f":{parts.port}"
    return urlunsplit((parts.scheme, host, parts.path.rstrip("/") or "/",
                       urlencode(sorted(query, key=lambda item: item[0])), ""))


def _public_url(url: str):
    host = urlsplit(normalize_url(url)).hostname
    addresses = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise ValueError("Seules les adresses web publiques sont autorisées")


def fetch_html(url: str) -> dict:
    url = normalize_url(url)
    with requests.Session() as session:
        for _ in range(6):
            _public_url(url)
            with session.get(url, headers=HEADERS, timeout=(10, 25), stream=True,
                             allow_redirects=False) as response:
                if response.status_code in {301, 302, 303, 307, 308}:
                    url = normalize_url(urljoin(url, response.headers.get("Location", "")))
                    continue
                response.raise_for_status()
                mime = response.headers.get("Content-Type", "").lower()
                if not any(value in mime for value in ("text/html", "application/xhtml+xml")):
                    raise ValueError("La réponse n'est pas une page HTML")
                chunks, size = [], 0
                for chunk in response.iter_content(65536):
                    size += len(chunk)
                    if size > MAX_BYTES:
                        raise ValueError("Page HTML supérieure à 5 Mo")
                    chunks.append(chunk)
                content = b"".join(chunks)
                # BeautifulSoup détecte le charset déclaré dans le HTML.
                return {"url": url, "bytes": content,
                        "html": str(BeautifulSoup(content, "html.parser"))}
    raise ValueError("Trop de redirections HTTP")


def _host(url: str):
    return (urlsplit(url).hostname or "").lower().removeprefix("www.")


def in_scope(url: str, source_url: str, prefix: str) -> bool:
    try:
        url = normalize_url(url)
    except (ValueError, TypeError):
        return False
    path = urlsplit(url).path
    prefix = prefix.rstrip("/") or "/"
    return _host(url) == _host(source_url) and (
        prefix == "/" or path == prefix or path.startswith(prefix + "/")
    )


def discover(watch: dict) -> dict:
    config = watch.get("collection_config") or {}
    source_url = normalize_url(watch["source_url"])
    mode = config.get("mode", "LISTING")
    if mode == "SINGLE_PAGE":
        return {"items": [{"url": source_url}], "pages_scanned": 0,
                "warnings": ["Périmètre : cette page uniquement."]}
    if mode != "LISTING":
        raise ValueError("collection_config.mode : LISTING ou SINGLE_PAGE attendu")
    max_urls = config.get("max_urls", 500)
    if type(max_urls) is not int or not 1 <= max_urls <= 500:
        raise ValueError("max_urls doit être compris entre 1 et 500")
    prefix = config.get("path_prefix") or urlsplit(source_url).path.rstrip("/") or "/"
    if not isinstance(prefix, str) or not prefix.startswith("/"):
        raise ValueError("path_prefix doit commencer par /")
    selector = config.get("link_selector") or "a[href]"
    # One configured document only. No article, author or pagination request.
    page = fetch_html(source_url)
    if _host(page["url"]) != _host(source_url):
        raise ValueError("La page configurée redirige vers un autre domaine")
    soup = BeautifulSoup(page["html"], "html.parser")
    seen, items = set(), []
    warnings = ["Page configurée uniquement ; pagination non suivie."]
    # Do not propose navigation controls as content to store.
    pagination_nodes = {id(node) for node in soup.select(
        'a[rel~="next"], a[rel~="prev"], .pagination a[href], .w-pagination-wrapper a[href], '
        '[aria-label*="pagination" i] a[href]')}
    self_keys = {url_key(source_url), url_key(page["url"])}
    source_path = urlsplit(page["url"]).path.rstrip("/") or "/"
    for link in soup.select(selector):
        if id(link) in pagination_nodes:
            continue
        href = link.get("href")
        if not href:
            continue
        try:
            url = normalize_url(urljoin(page["url"], href))
            key = url_key(url)
        except (ValueError, TypeError):
            continue
        if not in_scope(url, source_url, prefix) or key in seen or key in self_keys:
            continue
        target = urlsplit(url)
        query_keys = {key.lower() for key, _ in parse_qsl(target.query)}
        if (target.path.rstrip("/") or "/") == source_path and any(
            key in {"page", "paged", "pageno", "pg"} or key.endswith("_page") for key in query_keys
        ):
            continue
        if re.fullmatch(re.escape(source_path.rstrip("/")) + r"/page/\d+/?", target.path):
            continue
        if re.search(r"\.(?:png|jpg|jpeg|gif|svg|zip|pdf|mp4)(?:$|\?)", url, re.I):
            continue
        seen.add(key)
        if len(items) >= max_urls:
            warnings.append("Limite max_urls atteinte sur cette page ; augmenter le paramètre.")
            break
        items.append({"url": url, "title": link.get_text(" ", strip=True) or url})
    if not items:
        warnings.append("Aucune URL détectée : vérifier le périmètre, le sélecteur ou une page de connexion.")
    return {"items": items, "pages_scanned": 1, "warnings": warnings}


def parse_html(html: str, url: str, config: dict) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    date_value = None
    for attributes in ({"property": "article:published_time"}, {"itemprop": "datePublished"},
                       {"name": "date"}):
        node = soup.find("meta", attributes)
        if node and node.get("content"):
            date_value = node["content"]
            break
    if not date_value:
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                values = json.loads(script.string or script.get_text() or "{}")
                values = values if isinstance(values, list) else [values]
                pending = list(values)
                while pending:
                    value = pending.pop(0)
                    if not isinstance(value, dict):
                        continue
                    if value.get("datePublished"):
                        date_value = value["datePublished"]
                        break
                    if isinstance(value.get("@graph"), list):
                        pending.extend(value["@graph"])
                if date_value:
                    break
            except (ValueError, TypeError):
                continue
    if not date_value:
        node = soup.find("time", datetime=True)
        date_value = node.get("datetime") if node else None
    published = None
    if date_value:
        try:
            published = parse_date(date_value).isoformat()
        except (ValueError, OverflowError, TypeError):
            pass
    selector = config.get("content_selector")
    region = soup.select_one(selector) if selector else (soup.find("article") or soup.find("main") or soup.body)
    if region is None:
        raise ValueError("Zone de contenu introuvable : vérifier content_selector")
    title_node = region.find("h1") or soup.find("h1") or soup.title
    title = title_node.get_text(" ", strip=True) if title_node else url
    for node in region.select("script,style,noscript,nav,form,button,[aria-hidden='true']"):
        node.decompose()
    if region.name == "body":
        for node in region.select("header,footer"):
            node.decompose()
    # Conserver titres/listes/tableaux et séparer les blocs sans limiter aux <p>.
    text = region.get_text("\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        raise ValueError("Texte vide")
    lower = text.casefold()
    if len(text) < 6000 and any(s in lower for s in (
        "sign in to view", "join linkedin to", "authwall", "verify you are human", "checking your browser"
    )):
        raise ValueError("Page de connexion ou de protection reçue ; utiliser un autre mode de récupération")
    return {"title": title, "text": text, "published_at": published,
            "date_precision": "SOURCE" if published else "UNKNOWN"}

