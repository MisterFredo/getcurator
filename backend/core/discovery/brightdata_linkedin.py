"""Reusable LinkedIn transport/normalization. No Company, RAW or Library writes."""
from __future__ import annotations

import os
import logging
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit

import requests

API = "https://api.brightdata.com/datasets/v3"
DATASET = "gd_lyy3tktm25m4avu764"


logger = logging.getLogger(__name__)


def safe_error_text(value, limit=1200):
    text = str(value)
    token = os.getenv("BRIGHTDATA_API_KEY", "").strip()
    if token:
        text = text.replace(token, "[masqué]")
    text = re.sub(r"(?i)bearer\s+[^\s\"'<>]+", "Bearer [masqué]", text)
    text = re.sub(r"(?i)((?:api[_-]?key|access[_-]?token|token|password|authorization)[\"']?\s*[:=]\s*)[^\s,;<>]+", r"\1[masqué]", text)
    return " ".join(text.split())[:limit]


class ProviderError(RuntimeError):
    def __init__(self, message, *, diagnostic=None):
        super().__init__(safe_error_text(message))
        self.diagnostic = diagnostic or {}


def error_diagnostic(error):
    # No URL, account input, request body or Authorization header is stored.
    return {**getattr(error, "diagnostic", {}), "message": safe_error_text(error)}


def response_diagnostic(response, phase):
    headers = {str(k).lower(): v for k, v in (response.headers or {}).items()}
    diagnostic = {"phase": phase, "http_status": response.status_code}
    for name in ("x-request-id", "x-brd-request-id", "retry-after"):
        value = headers.get(name)
        if value:
            diagnostic[name.replace("-", "_")] = safe_error_text(value, 150)
    try:
        data = response.json()
    except ValueError:
        data = None
    fields = ("error", "message", "code", "error_code", "detail", "details", "errors", "description")
    def messages(value, depth=0):
        if depth > 3:
            return []
        if isinstance(value, dict):
            return [text for key in fields if key in value for text in messages(value[key], depth+1)]
        if isinstance(value, list):
            return [text for item in value[:5] for text in messages(item, depth+1)]
        if isinstance(value, (str, int, float)):
            return [safe_error_text(value, 500)]
        return []
    excerpts = messages(data) if isinstance(data, dict) else []
    if excerpts:
        diagnostic["provider_message"] = safe_error_text(" | ".join(dict.fromkeys(excerpts)))
    elif data is None:
        diagnostic["provider_message"] = safe_error_text(response.text, 700)
    return diagnostic



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
    # One request only. In particular, no retry of paid POSTs.
    method = method.upper()
    phase = "trigger" if method == "POST" else "read"
    try:
        response = requests.request(method, API + path,
            headers={"Authorization": "Bearer " + _token(), "Content-Type": "application/json"},
            timeout=(10, 60), allow_redirects=False, **kwargs)
    except requests.RequestException as exc:
        error = AmbiguousTrigger if method == "POST" else ProviderError
        diagnostic = {"phase": phase, "transport_error": type(exc).__name__}
        raise error("Bright Data : réponse réseau indisponible (" + type(exc).__name__ + ").",
                    diagnostic=diagnostic) from None
    if not 200 <= response.status_code < 300:
        diagnostic = response_diagnostic(response, phase)
        error = AmbiguousTrigger if method == "POST" and (response.status_code >= 500 or response.status_code == 408) else ProviderError
        message = "Bright Data HTTP " + str(response.status_code)
        if diagnostic.get("provider_message"):
            message += " : " + diagnostic["provider_message"]
        if diagnostic.get("retry_after"):
            message += " ; Retry-After : " + diagnostic["retry_after"]
        logger.warning("[BRIGHTDATA] %s", safe_error_text(message))
        raise error(message, diagnostic=diagnostic)
    try:
        return response.json()
    except ValueError:
        error = AmbiguousTrigger if method == "POST" else ProviderError
        raise error("Bright Data HTTP " + str(response.status_code) + " : réponse JSON invalide",
                    diagnostic={"phase": phase, "http_status": response.status_code}) from None


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
        detail = " | ".join(safe_error_text(result[key], 350)
            for key in ("error", "message", "code", "error_code", "detail")
            if isinstance(result, dict) and isinstance(result.get(key), (str, int)))
        message = "Bright Data : lancement sans identifiant"
        if detail:
            message += " : " + detail
        raise AmbiguousTrigger(message + " ; vérifier la console avant une nouvelle collecte",
            diagnostic={"phase": "trigger", "provider_message": detail}) from None


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
