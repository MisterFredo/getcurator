"""Reusable LinkedIn transport/normalization. No Company, RAW or Library writes."""
from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit

import requests

API = "https://api.brightdata.com/datasets/v3"
DATASET = "gd_lyy3tktm25m4avu764"


class ProviderError(RuntimeError):
    pass


class AmbiguousTrigger(ProviderError):
    """Request might have reached the provider. Never retry a paid POST automatically."""


def account_url(value):
    parts = urlsplit(value)
    host = (parts.hostname or "").lower()
    if (parts.scheme not in {"http", "https"} or
            not (host == "linkedin.com" or host.endswith(".linkedin.com")) or
            parts.username or parts.password or parts.port not in (None, 80, 443)):
        raise ValueError("Une URL de société ou de profil LinkedIn est requise")
    match = re.fullmatch(r"/(company|in)/([^/]+)(?:/.*)?", parts.path)
    if not match:
        raise ValueError("URL attendue : linkedin.com/company/… ou linkedin.com/in/…")
    kind, slug = match.groups()
    return f"https://www.linkedin.com/{kind}/{slug}", "company_url" if kind == "company" else "profile_url"


def validate_config(url, config):
    account_url(url)
    # 100 records by default. null explicitly requests no provider-side cap.
    limit = config.get("limit_per_input", 100)
    if limit is not None and (type(limit) is not int or not 1 <= limit <= 10000):
        raise ValueError("limit_per_input : entier de 1 à 10000, ou null")
    return limit


def _token():
    token = os.getenv("BRIGHTDATA_API_KEY", "").strip()
    if not token:
        raise ProviderError("BRIGHTDATA_API_KEY manquante dans le backend")
    return token


def _request(method, path, **kwargs):
    # Fixed API origin, no credential-bearing redirects, no automatic POST retry.
    try:
        response = requests.request(method, API + path,
            headers={"Authorization": "Bearer " + _token(), "Content-Type": "application/json"},
            timeout=(10, 60), allow_redirects=False, **kwargs)
    except requests.RequestException:
        error = AmbiguousTrigger if method == "POST" else ProviderError
        raise error("Bright Data : réponse réseau indisponible. Réessayer la récupération du résultat.") from None
    if not 200 <= response.status_code < 300:
        error = AmbiguousTrigger if method == "POST" and response.status_code >= 500 else ProviderError
        raise error(f"Bright Data HTTP {response.status_code} : vérifier le compte, la clé et les paramètres.")
    try:
        return response.json()
    except ValueError:
        error = AmbiguousTrigger if method == "POST" else ProviderError
        raise error("Bright Data : réponse JSON invalide") from None


def _snapshot(value):
    if not isinstance(value, str) or not re.fullmatch(r"sd_[A-Za-z0-9_-]+", value):
        raise ValueError("Identifiant de collecte Bright Data invalide")
    return value


def trigger(url, config):
    url, discover_by = account_url(url)
    limit = validate_config(url, config)
    _token()  # fail before issuing a paid request
    result = _request("POST", "/trigger", params={"dataset_id": DATASET,
        "notify": "false", "include_errors": "true", "type": "discover_new", "discover_by": discover_by},
        json={"input": [{"url": url}], "limit_per_input": limit})
    try:
        return _snapshot(result["snapshot_id"])
    except (KeyError, TypeError, ValueError):
        raise AmbiguousTrigger("Bright Data : lancement sans identifiant ; vérifier la console avant une nouvelle collecte") from None


def progress(snapshot):
    result = _request("GET", "/progress/" + _snapshot(snapshot))
    if not isinstance(result, dict) or result.get("status") not in {"starting", "running", "ready", "failed", "canceled"}:
        raise ProviderError("Bright Data : état de collecte non reconnu")
    return result["status"]


def download(snapshot):
    result = _request("GET", "/snapshot/" + _snapshot(snapshot), params={"format": "json"})
    if not isinstance(result, list):
        raise ProviderError("Bright Data : résultat attendu sous forme de liste")
    return result


def post_id(value):
    """Stable identity across fr/www URLs, slugs and feed/update URNs."""
    try:
        parts = urlsplit(value)
        host = (parts.hostname or "").lower()
        if host != "linkedin.com" and not host.endswith(".linkedin.com"):
            return None
        match = re.search(r"(?:activity-|urn:li:(?:activity|share|ugcPost):)(\d+)", parts.path)
        return match.group(1) if match else None
    except (ValueError, TypeError):
        return None


def normalize_records(records):
    posts, issues, seen = [], [], set()
    for index, raw in enumerate(records):
        if not isinstance(raw, dict):
            issues.append({"index": index, "reason": "INVALID_RECORD"}); continue
        identifier, text, url = raw.get("id"), raw.get("post_text"), raw.get("url")
        identifier = str(identifier or "")
        if raw.get("error") or raw.get("error_code"):
            issues.append({"index": index, "reason": "PROVIDER_ERROR"}); continue
        if not identifier.isdigit() or post_id(url) != identifier or not isinstance(text, str) or not text.strip():
            issues.append({"index": index, "reason": "MISSING_OR_INVALID_POST"}); continue
        if identifier in seen:
            continue
        seen.add(identifier)
        date = raw.get("date_posted")
        try:
            parsed = datetime.fromisoformat(date.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                raise ValueError()
            date = parsed.astimezone(timezone.utc).isoformat()
        except (ValueError, TypeError, AttributeError):
            date = None
            issues.append({"index": index, "reason": "MISSING_PUBLICATION_DATE"})
        posts.append({"post_id": identifier, "url": f"https://www.linkedin.com/feed/update/urn:li:activity:{identifier}",
            "original_url": url, "text": text.strip(), "published_at": date,
            "author_id": raw.get("user_id"), "author_name": raw.get("user_name"),
            "author_url": raw.get("use_url"), "repost": raw.get("repost"), "raw": raw})
    posts.sort(key=lambda p: p["published_at"] or "", reverse=True)
    return posts, issues
