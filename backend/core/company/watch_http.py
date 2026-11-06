"""Dedicated HTML acquisition. Never calls the media Discovery service."""
from __future__ import annotations

import ipaddress
import json
import re
import socket
from urllib.parse import urljoin, urlsplit, urlunsplit

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
    max_pages = config.get("max_pages", 5)
    max_urls = config.get("max_urls", 100)
    if type(max_pages) is not int or not 1 <= max_pages <= 20:
        raise ValueError("max_pages doit être compris entre 1 et 20")
    if type(max_urls) is not int or not 1 <= max_urls <= 500:
        raise ValueError("max_urls doit être compris entre 1 et 500")
    prefix = config.get("path_prefix") or urlsplit(source_url).path.rstrip("/") or "/"
    if not isinstance(prefix, str) or not prefix.startswith("/"):
        raise ValueError("path_prefix doit commencer par /")
    selector = config.get("link_selector") or "a[href]"
    next_selector = config.get("next_selector") or 'a[rel~="next"]'
    page_url, visited, seen, items, warnings = source_url, set(), set(), [], []
    while page_url and len(visited) < max_pages:
        if page_url in visited:
            warnings.append("Pagination en boucle : arrêt explicite.")
            break
        # Une erreur de pagination ne doit pas annuler les URL déjà découvertes.
        try:
            page = fetch_html(page_url)
        except Exception as exc:
            if not visited:
                raise
            warnings.append(f"Pagination interrompue sur {page_url} : {exc}")
            break
        if _host(page["url"]) != _host(source_url):
            raise ValueError("La page de liste redirige vers un autre domaine")
        visited.add(page_url)
        soup = BeautifulSoup(page["html"], "html.parser")
        next_node = soup.select_one(next_selector)
        next_url = None
        if next_node and next_node.get("href"):
            try:
                candidate = normalize_url(urljoin(page["url"], next_node["href"]))
                if _host(candidate) == _host(source_url):
                    next_url = candidate
            except ValueError:
                pass
        for link in soup.select(selector):
            href = link.get("href")
            if not href:
                continue
            try:
                url = normalize_url(urljoin(page["url"], href))
            except ValueError:
                continue
            if not in_scope(url, source_url, prefix) or url in seen:
                continue
            if url in {source_url, page_url, page["url"], next_url}:
                continue
            # Pas d'exclusions éditoriales /about, /contact, etc.
            if re.search(r"\.(?:png|jpg|jpeg|gif|svg|zip|pdf|mp4)(?:$|\?)", url, re.I):
                continue
            seen.add(url)
            if len(items) >= max_urls:
                warnings.append("Limite max_urls atteinte : collecte partielle, augmenter le paramètre.")
                return {"items": items, "pages_scanned": len(visited), "warnings": warnings}
            items.append({"url": url, "title": link.get_text(" ", strip=True) or url})
        page_url = next_url
    if page_url and len(visited) >= max_pages:
        warnings.append("Limite max_pages atteinte : pagination restante non parcourue.")
    warnings.append("Couverture limitée aux liens HTML et à la pagination exposés dans le périmètre configuré.")
    if not items:
        warnings.append("Aucune URL détectée : vérifier le périmètre, le sélecteur ou une page de connexion.")
    return {"items": items, "pages_scanned": len(visited), "warnings": warnings}


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
