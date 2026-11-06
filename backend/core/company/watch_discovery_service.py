"""Corpo: scan -> durable discovery -> selected immutable stock. No LLM calls."""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from urllib.parse import urlsplit

from fastapi import HTTPException
from google.cloud import bigquery

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import get_bigquery_client
from core.company.watch_service import get_company_watch, _company
from core.company.watch_http import discover, fetch_html, parse_html, normalize_url, in_scope
# Reuse only storage and locking helpers. No register_publication/extract_step call.
from core.library.company_watch_library import _upload, _read_uri, document_lock

BASE = f"{BQ_PROJECT}.{BQ_DATASET}"
DISCOVERY = f"{BASE}.RATECARD_COMPANY_WATCH_DISCOVERY"
STOCK = f"{BASE}.RATECARD_COMPANY_WATCH_STOCK"
DOCUMENT = f"{BASE}.RATECARD_SOURCE_DOCUMENT"
WATCH = f"{BASE}.RATECARD_COMPANY_WATCH"
COMPANY = f"{BASE}.RATECARD_COMPANY"


def _p(name, kind, value):
    return bigquery.ScalarQueryParameter(name, kind, value)


def _query(sql, params=()):
    return list(get_bigquery_client().query(sql, job_config=bigquery.QueryJobConfig(
        query_parameters=list(params))).result())


def active_watch(company_id, watch_id):
    watch = get_company_watch(company_id, watch_id)
    _company(company_id, require_active=True)
    if not watch["is_active"]:
        raise HTTPException(409, "Point de collecte suspendu")
    return watch


def effective_mode(watch):
    config = watch.get("collection_config") or {}
    host = (urlsplit(watch["source_url"]).hostname or "").lower()
    default = "SINGLE_PAGE" if host == "linkedin.com" or host.endswith(".linkedin.com") else "LISTING"
    mode = config.get("mode", default)
    if mode not in {"LISTING", "SINGLE_PAGE"}:
        raise ValueError("mode doit être LISTING ou SINGLE_PAGE")
    return mode


def _capture(watch, url):
    page = fetch_html(url)
    if not in_scope(page["url"], watch["source_url"], "/"):
        raise ValueError("La publication redirige hors du domaine suivi")
    parsed = parse_html(page["html"], page["url"], watch.get("collection_config") or {})
    raw_hash = hashlib.sha256(page["bytes"]).hexdigest()
    text_hash = hashlib.sha256(parsed["text"].encode()).hexdigest()
    path = f"company-watch/captures/{watch['id_company_watch']}/{raw_hash}"
    raw_uri = _upload(f"{path}/original.html", page["bytes"], "text/html")
    text_uri = _upload(f"{path}/text-{text_hash}.txt", parsed["text"].encode(), "text/plain; charset=utf-8")
    captured = datetime.now(timezone.utc).isoformat()
    metadata = {"url": page["url"], "requested_url": url, "title": parsed["title"],
        "published_at": parsed["published_at"], "date_precision": parsed["date_precision"],
        "captured_at": captured, "original_sha256": raw_hash, "content_sha256": text_hash,
        "storage_uri": raw_uri, "text_storage_uri": text_uri,
        "id_company": watch["id_company"], "id_company_watch": watch["id_company_watch"],
        "source_role": watch["source_role"], "author_name": watch.get("author_name"),
        "collection_config": watch.get("collection_config") or {}}
    # Unique capture record: configuration and acquisition date also have provenance.
    uri = _upload(f"{path}/{uuid.uuid4().hex}.json", json.dumps(metadata, ensure_ascii=False).encode(), "application/json")
    return metadata, uri


def _last_observation(watch_id, url):
    rows = _query(f"""SELECT * FROM `{DISCOVERY}`
        WHERE ID_COMPANY_WATCH=@watch AND URL=@url
        ORDER BY DATE_FOUND DESC, ID_DISCOVERY DESC LIMIT 1""",
        [_p("watch", "STRING", watch_id), _p("url", "STRING", url)])
    return dict(rows[0]) if rows else None


def _legacy_hash(watch_id, url):
    rows = _query(f"""SELECT CONTENT_SHA256 FROM `{DOCUMENT}`
        WHERE ID_COMPANY_WATCH=@watch AND SOURCE_URL=@url
        ORDER BY COLLECTED_AT DESC LIMIT 1""",
        [_p("watch", "STRING", watch_id), _p("url", "STRING", url)])
    return rows[0]["CONTENT_SHA256"] if rows else None


def _insert_candidate(watch, url, title, change, *, content_hash=None, snapshot=None):
    candidate_id = str(uuid.uuid4())
    params = [_p("id", "STRING", candidate_id), _p("company", "STRING", watch["id_company"]),
        _p("watch", "STRING", watch["id_company_watch"]), _p("url", "STRING", url),
        _p("title", "STRING", title), _p("change", "STRING", change),
        _p("hash", "STRING", content_hash), _p("snapshot", "STRING", snapshot)]
    _query(f"""INSERT INTO `{DISCOVERY}` (ID_DISCOVERY, ID_COMPANY, ID_COMPANY_WATCH,
        URL, TITLE, CHANGE_TYPE, STATUS, CONTENT_SHA256, SNAPSHOT_URI, DATE_FOUND, LAST_SEEN_AT, UPDATED_AT)
        VALUES (@id, @company, @watch, @url, @title, @change, 'NEW', @hash, @snapshot,
          CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP())""", params)
    return candidate_id


def _touch(candidate_id):
    _query(f"UPDATE `{DISCOVERY}` SET LAST_SEEN_AT=CURRENT_TIMESTAMP() WHERE ID_DISCOVERY=@id",
           [_p("id", "STRING", candidate_id)])


def scan_watch(company_id, watch_id):
    watch = active_watch(company_id, watch_id)
    if watch["collection_method"] != "HTML" or watch["source_type"] == "PDF":
        raise ValueError("Le scan nécessite un point HTML actif")
    # Un scan par point à la fois, indépendamment des autres sociétés.
    with document_lock("scan-" + watch_id):
        url = normalize_url(watch["source_url"])
        mode = effective_mode(watch)
        new, known, unchanged, warnings = 0, 0, 0, []
        if mode == "SINGLE_PAGE":
            # Lire est nécessaire pour constater une modification. Cette capture
            # temporaire n'entre dans le stock qu'après sélection explicite.
            metadata, snapshot = _capture(watch, url)
            previous = _last_observation(watch_id, url)
            baseline = previous.get("CONTENT_SHA256") if previous else _legacy_hash(watch_id, metadata["url"])
            if baseline and baseline == metadata["content_sha256"]:
                if previous:
                    _touch(previous["ID_DISCOVERY"])
                unchanged = 1
            else:
                _insert_candidate(watch, url, metadata["title"], "UPDATED_PAGE" if baseline else "NEW_PAGE",
                                  content_hash=metadata["content_sha256"], snapshot=snapshot)
                new = 1
            warnings = ["Comparaison du texte utile de cette page uniquement ; régler content_selector pour une zone stable."]
        else:
            result = discover({**watch, "collection_config": {**(watch.get("collection_config") or {}), "mode": "LISTING"}})
            warnings = result.get("warnings") or []
            # Ne lire ni capturer les articles au stade de la découverte d'URL.
            existing = _query(f"SELECT URL FROM `{DISCOVERY}` WHERE ID_COMPANY_WATCH=@watch",
                              [_p("watch", "STRING", watch_id)])
            legacy = _query(f"SELECT SOURCE_URL FROM `{DOCUMENT}` WHERE ID_COMPANY_WATCH=@watch",
                            [_p("watch", "STRING", watch_id)])
            urls = {r["URL"] for r in existing} | {r["SOURCE_URL"] for r in legacy if r["SOURCE_URL"]}
            for item in result["items"]:
                target = normalize_url(item["url"])
                if target in urls:
                    known += 1
                    continue
                _insert_candidate(watch, target, item.get("title"), "NEW_URL")
                urls.add(target)
                new += 1
        return {"status": "ok", "new": new, "known": known, "unchanged": unchanged, "warnings": warnings}


def list_candidates(company_id=None, watch_id=None, status="NEW", offset=0, limit=50):
    if status not in {"NEW", "STORED", "ALL"}:
        raise ValueError("Statut invalide")
    clauses, params = [], []
    if company_id:
        clauses.append("d.ID_COMPANY=@company"); params.append(_p("company", "STRING", company_id))
    if watch_id:
        clauses.append("d.ID_COMPANY_WATCH=@watch"); params.append(_p("watch", "STRING", watch_id))
    if status != "ALL":
        clauses.append("d.STATUS=@status"); params.append(_p("status", "STRING", status))
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    params += [_p("limit", "INT64", limit + 1), _p("offset", "INT64", offset)]
    rows = _query(f"""SELECT d.*, w.LABEL AS WATCH_LABEL, c.NAME AS COMPANY_NAME,
        w.IS_ACTIVE AS WATCH_ACTIVE, w.COLLECTION_METHOD
        FROM `{DISCOVERY}` d LEFT JOIN `{WATCH}` w USING (ID_COMPANY_WATCH, ID_COMPANY)
        LEFT JOIN `{COMPANY}` c ON c.ID_COMPANY=d.ID_COMPANY {where}
        ORDER BY d.DATE_FOUND DESC, d.ID_DISCOVERY DESC LIMIT @limit OFFSET @offset""", params)
    return {"items": [{k.lower(): v for k,v in dict(r).items()} for r in rows[:limit]],
            "has_more": len(rows)>limit, "offset": offset, "limit": limit}


def get_candidate(candidate_id):
    rows = _query(f"SELECT * FROM `{DISCOVERY}` WHERE ID_DISCOVERY=@id LIMIT 1",
                  [_p("id", "STRING", candidate_id)])
    if not rows:
        raise HTTPException(404, "URL découverte introuvable")
    return dict(rows[0])


def store_candidate(candidate_id):
    with document_lock("stock-" + candidate_id):
        candidate = get_candidate(candidate_id)
        if candidate["STATUS"] == "STORED":
            return {"status": "STORED", "id_stock": candidate["ID_STOCK"], "already_exists": True}
        if candidate["STATUS"] != "NEW":
            raise HTTPException(409, "Cette URL n'est pas disponible pour stockage")
        watch = active_watch(candidate["ID_COMPANY"], candidate["ID_COMPANY_WATCH"])
        if watch["collection_method"] != "HTML":
            raise HTTPException(409, "Ce point n'est plus configuré en HTML")
        try:
            if candidate.get("SNAPSHOT_URI"):
                metadata_uri = candidate["SNAPSHOT_URI"]
                metadata = json.loads(_read_uri(metadata_uri))
            else:
                metadata, metadata_uri = _capture(watch, candidate["URL"])
                # Fixer la capture avant la transaction pour une reprise idempotente.
                _query(f"""UPDATE `{DISCOVERY}` SET SNAPSHOT_URI=@snapshot,
                    CONTENT_SHA256=@hash, UPDATED_AT=CURRENT_TIMESTAMP() WHERE ID_DISCOVERY=@id""",
                    [_p("snapshot", "STRING", metadata_uri), _p("hash", "STRING", metadata["content_sha256"]),
                     _p("id", "STRING", candidate_id)])
            stock_id = str(uuid.uuid5(uuid.NAMESPACE_URL, "corpo-stock:" + candidate_id))
            params = [_p("watch", "STRING", candidate["ID_COMPANY_WATCH"]), _p("url", "STRING", candidate["URL"])]
            previous = _query(f"""SELECT ID_STOCK FROM `{STOCK}` WHERE ID_COMPANY_WATCH=@watch
                AND URL=@url ORDER BY STORED_AT DESC LIMIT 1""", params)
            values = {"id": stock_id, "discovery": candidate_id, "company": candidate["ID_COMPANY"],
                "watch": candidate["ID_COMPANY_WATCH"], "url": candidate["URL"], "title": metadata["title"],
                "change": candidate["CHANGE_TYPE"], "previous": previous[0]["ID_STOCK"] if previous else None,
                "hash": metadata["content_sha256"], "raw_hash": metadata["original_sha256"],
                "uri": metadata["storage_uri"], "text_uri": metadata["text_storage_uri"],
                "metadata": metadata_uri, "captured": metadata["captured_at"]}
            _query(f"""BEGIN TRANSACTION;
                MERGE `{STOCK}` T USING (SELECT @id AS ID_STOCK) S ON T.ID_STOCK=S.ID_STOCK
                WHEN NOT MATCHED THEN INSERT (ID_STOCK, ID_DISCOVERY, ID_COMPANY, ID_COMPANY_WATCH,
                  URL, TITLE, CHANGE_TYPE, PREVIOUS_STOCK_ID, CONTENT_SHA256, ORIGINAL_SHA256,
                  STORAGE_URI, TEXT_STORAGE_URI, METADATA_STORAGE_URI, CAPTURED_AT, STORED_AT, STATUS)
                VALUES (@id, @discovery, @company, @watch, @url, @title, @change, @previous,
                  @hash, @raw_hash, @uri, @text_uri, @metadata, CAST(@captured AS TIMESTAMP), CURRENT_TIMESTAMP(), 'STORED');
                UPDATE `{DISCOVERY}` SET STATUS='STORED', ID_STOCK=@id, TITLE=@title, ERROR=NULL,
                  UPDATED_AT=CURRENT_TIMESTAMP() WHERE ID_DISCOVERY=@discovery;
                COMMIT TRANSACTION;""", [_p(k,"STRING",v) for k,v in values.items()])
            return {"status": "STORED", "id_stock": stock_id, "already_exists": False}
        except Exception as exc:
            _query(f"UPDATE `{DISCOVERY}` SET ERROR=@error, UPDATED_AT=CURRENT_TIMESTAMP() WHERE ID_DISCOVERY=@id",
                [_p("error", "STRING", str(exc)[:3000]), _p("id", "STRING", candidate_id)])
            raise


def candidate_detail(candidate_id):
    candidate = get_candidate(candidate_id)
    if candidate["STATUS"] != "STORED" or not candidate.get("SNAPSHOT_URI"):
        raise HTTPException(409, "Le contenu n'est consultable qu'après stockage")
    metadata = json.loads(_read_uri(candidate["SNAPSHOT_URI"]))
    return {"title": metadata["title"], "url": metadata["url"],
            "captured_at": metadata["captured_at"], "text": _read_uri(metadata["text_storage_uri"])}
