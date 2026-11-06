"""Orchestration Corpo. One request per acquisition or extraction segment."""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

from fastapi import HTTPException

from core.company.watch_service import get_company_watch, _company
from core.company.watch_http import discover, fetch_html, parse_html, normalize_url, in_scope
from core.library.company_watch_library import register_publication, _upload


def active_watch(company_id: str, watch_id: str) -> dict:
    watch = get_company_watch(company_id, watch_id)
    _company(company_id, require_active=True)
    if not watch["is_active"]:
        raise HTTPException(409, "Point de collecte suspendu")
    return watch


def scan_watch(company_id: str, watch_id: str) -> dict:
    watch = active_watch(company_id, watch_id)
    if watch["collection_method"] != "HTML":
        raise ValueError("Choisir la méthode HTML pour collecter le web ; utiliser Importer pour Manuel/Studio")
    if watch["source_type"] == "PDF":
        raise ValueError("Utiliser PDF Studio pour l'import PDF dans cette version")
    # Un fil LinkedIn peut être capturé comme une page complète plutôt que traité
    # comme une liste de liens d'articles. L'admin peut surcharger ce réglage.
    config = {**(watch.get("collection_config") or {})}
    if "linkedin.com" in (normalize_url(watch["source_url"]).split("/")[2]):
        config.setdefault("mode", "SINGLE_PAGE")
    result = discover({**watch, "collection_config": config})
    scan_id = str(uuid.uuid4())
    _upload(f"company-watch/scans/{watch_id}/{scan_id}.json", json.dumps({
        "id_scan": scan_id, "id_company": company_id, "id_company_watch": watch_id,
        "source_url": watch["source_url"], "config": config,
        "collected_at": datetime.now(timezone.utc).isoformat(), **result,
    }, ensure_ascii=False).encode(), "application/json")
    return {"status": "ok", "id_scan": scan_id, **result}


def collect_url(company_id: str, watch_id: str, url: str) -> dict:
    watch = active_watch(company_id, watch_id)
    if watch["collection_method"] != "HTML" or watch["source_type"] == "PDF":
        raise ValueError("Ce point n'est pas configuré pour la collecte HTML")
    config = watch.get("collection_config") or {}
    url = normalize_url(url)
    # Domaine identique, et chemin explicitement paramétrable.
    prefix = config.get("path_prefix") or "/"
    if not in_scope(url, watch["source_url"], prefix):
        raise ValueError("URL hors du périmètre du point de collecte")
    response = fetch_html(url)
    if not in_scope(response["url"], watch["source_url"], prefix):
        raise ValueError("Redirection hors du périmètre")
    parsed = parse_html(response["html"], response["url"], config)
    return register_publication(watch, source_url=response["url"], original=response["bytes"],
        text=parsed["text"], title=parsed["title"], mime="text/html",
        published_at=parsed["published_at"], date_precision=parsed["date_precision"],
        extra={"requested_url": url, "method": "HTML"})


def import_text(company_id: str, watch_id: str, data) -> dict:
    watch = active_watch(company_id, watch_id)
    if watch["source_type"] == "PDF":
        raise ValueError("Utiliser PDF Studio pour les PDF")
    text = data.text.strip()
    if not text:
        raise ValueError("Texte vide")
    paste_hash = hashlib.sha256(text.encode()).hexdigest()
    paste_uri = _upload(f"company-watch/imports/{watch_id}/{paste_hash}.txt", text.encode(), "text/plain; charset=utf-8")
    reference_date = data.reference_date or datetime.now(ZoneInfo("Europe/Paris")).date()
    if data.format == "LINKEDIN_ACTIVITY":
        from core.discovery.linkedin_studio import parse_linkedin_activity
        posts = parse_linkedin_activity(text, reference_date=reference_date)
        if not posts:
            raise ValueError("Aucune activité reconnue. Utiliser le format Publication unique pour ce texte.")
    else:
        posts = [{"raw_text": text, "title": data.title or watch["label"], "author": data.author_name,
                  "date_source": data.published_date, "activity_type": None}]
    items, errors = [], []
    for index, post in enumerate(posts):
        try:
            published = post.get("date_source")
            published = datetime.combine(published, time.min, tzinfo=timezone.utc).isoformat() if published else None
            # Sans permalink, le rattachement au compte est explicite dans les métadonnées.
            source_url = normalize_url(data.source_url or watch["source_url"])
            item = register_publication(watch, source_url=source_url,
                original=post["raw_text"].encode(), text=post["raw_text"],
                title=post.get("title") or watch["label"], mime="text/plain; charset=utf-8",
                published_at=published,
                date_precision="APPROXIMATE" if data.format == "LINKEDIN_ACTIVITY" else ("DAY" if published else "UNKNOWN"),
                author=post.get("author"), extra={"paste_uri": paste_uri,
                    "reference_date": reference_date.isoformat(), "activity_type": post.get("activity_type"),
                    "relative_date": post.get("relative_date"),
                    "url_precision": "ACCOUNT" if not data.source_url else "PROVIDED"})
            items.append(item)
        except Exception as exc:
            errors.append({"index": index, "error": str(exc)})
    return {"items": items, "errors": errors, "detected": len(posts),
            "warnings": ["Dates relatives approximatives. Sans URL individuelle, l'identité repose sur le compte et le texte.",
                         "Le découpage réutilise les formats reconnus par LinkedIn Studio ; le texte collé complet est conservé."]}
