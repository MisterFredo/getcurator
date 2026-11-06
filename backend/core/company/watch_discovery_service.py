"""Corpo: scan -> durable discovery -> selected immutable stock. No LLM calls."""
from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit

from fastapi import HTTPException
from google.cloud import bigquery

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import get_bigquery_client
from core.company.watch_service import get_company_watch, _company
from core.company.watch_http import discover, fetch_html, parse_html, normalize_url, in_scope, url_key
# Reuse only storage and locking helpers. No register_publication/extract_step call.
from core.library.company_watch_library import _upload, _read_uri, document_lock

BASE = f"{BQ_PROJECT}.{BQ_DATASET}"
DISCOVERY = f"{BASE}.RATECARD_COMPANY_WATCH_DISCOVERY"
STOCK = f"{BASE}.RATECARD_COMPANY_WATCH_STOCK"
DOCUMENT = f"{BASE}.RATECARD_SOURCE_DOCUMENT"
WATCH = f"{BASE}.RATECARD_COMPANY_WATCH"
COMPANY = f"{BASE}.RATECARD_COMPANY"
logger = logging.getLogger(__name__)


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


def _last_observation(company_id, url):
    rows = _query(f"""SELECT * FROM `{DISCOVERY}`
        WHERE ID_COMPANY=@company
        ORDER BY DATE_FOUND DESC, ID_DISCOVERY DESC""",
        [_p("company", "STRING", company_id)])
    key, pending = url_key(url), None
    for row in rows:
        try:
            matches = url_key(row["URL"]) == key
        except (ValueError, TypeError):
            continue
        if matches:
            if row.get("CONTENT_SHA256"):
                return dict(row)
            if pending is None:
                pending = dict(row)
    return pending


def _legacy_hash(company_id, url):
    rows = _query(f"""SELECT SOURCE_URL, CONTENT_SHA256 FROM `{DOCUMENT}`
        WHERE ID_COMPANY=@company AND ID_COMPANY_WATCH IS NOT NULL
        ORDER BY COLLECTED_AT DESC""", [_p("company", "STRING", company_id)])
    key = url_key(url)
    for row in rows:
        try:
            if row.get("SOURCE_URL") and url_key(row["SOURCE_URL"]) == key:
                return row["CONTENT_SHA256"]
        except (ValueError, TypeError):
            continue
    return None


def _known_keys(rows, column):
    keys = set()
    for row in rows:
        if not row.get(column):
            continue
        try:
            keys.add(url_key(row[column]))
        except (ValueError, TypeError):
            logger.warning("[CORPO SCAN] ignored malformed historical URL")
    return keys


def _bind_first_observation(previous, metadata, snapshot):
    # A URL ignored via a listing stays ignored if later configured as a
    # monitored page. Attach a baseline without inventing a new pending row.
    _query(f"""UPDATE `{DISCOVERY}` SET CONTENT_SHA256=@hash, SNAPSHOT_URI=@snapshot,
        LAST_SEEN_AT=CURRENT_TIMESTAMP(), UPDATED_AT=CURRENT_TIMESTAMP()
        WHERE ID_DISCOVERY=@id AND CONTENT_SHA256 IS NULL AND STATUS IN ('NEW', 'DISMISSED')""",
        [_p("hash", "STRING", metadata["content_sha256"]), _p("snapshot", "STRING", snapshot),
         _p("id", "STRING", previous["ID_DISCOVERY"])])


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


def _insert_candidates_batch(watch, items, *, batch_id=None):
    """One load job for all new listing URLs. Never stream or INSERT per URL."""
    if not items:
        return 0
    now = datetime.now(timezone.utc).isoformat()
    rows = [{
        "ID_DISCOVERY": str(uuid.uuid5(uuid.NAMESPACE_URL, batch_id + ":" + item["url"])) if batch_id else str(uuid.uuid4()),
        "ID_COMPANY": watch["id_company"],
        "ID_COMPANY_WATCH": watch["id_company_watch"],
        "URL": item["url"],
        "TITLE": item.get("title"),
        "CHANGE_TYPE": "NEW_URL",
        "STATUS": "NEW",
        "CONTENT_SHA256": item.get("content_hash"),
        "SNAPSHOT_URI": item.get("snapshot"),
        "ID_STOCK": None,
        "ERROR": None,
        "DATE_FOUND": now,
        "LAST_SEEN_AT": now,
        "UPDATED_AT": now,
    } for item in items]
    # Explicit schema: nullable columns are all null before content acquisition.
    required = {"ID_DISCOVERY", "ID_COMPANY", "ID_COMPANY_WATCH", "URL",
                "CHANGE_TYPE", "STATUS", "DATE_FOUND"}
    timestamps = {"DATE_FOUND", "LAST_SEEN_AT", "UPDATED_AT"}
    schema = [bigquery.SchemaField(
        column, "TIMESTAMP" if column in timestamps else "STRING",
        mode="REQUIRED" if column in required else "NULLABLE",
    ) for column in rows[0]]
    client = get_bigquery_client()
    config = bigquery.LoadJobConfig(schema=schema, write_disposition="WRITE_APPEND")
    if batch_id:
        # A response timeout must not create a second append job on recovery.
        from google.api_core.exceptions import Conflict
        job_id = "corpo_bd_" + hashlib.sha256(batch_id.encode()).hexdigest()
        try:
            job = client.load_table_from_json(rows, DISCOVERY, job_config=config, job_id=job_id)
        except Conflict:
            location = client.get_dataset(BASE).location
            job = client.get_job(job_id, location=location)
        job.result()
    else:
        client.load_table_from_json(rows, DISCOVERY, job_config=config).result()
    logger.info("[CORPO SCAN] watch=%s inserted=%d load_jobs=1", watch["id_company_watch"], len(rows))
    return len(rows)


def _touch(candidate_id):
    _query(f"UPDATE `{DISCOVERY}` SET LAST_SEEN_AT=CURRENT_TIMESTAMP() WHERE ID_DISCOVERY=@id",
           [_p("id", "STRING", candidate_id)])


def scan_watch(company_id, watch_id):
    watch = active_watch(company_id, watch_id)
    if watch["collection_method"] == "BRIGHTDATA":
        from core.company.watch_brightdata_service import scan_linkedin
        return scan_linkedin(company_id, watch_id, start=True)
    if watch["collection_method"] != "HTML" or watch["source_type"] == "PDF":
        raise ValueError("Le scan nécessite un point HTML ou Bright Data actif")
    # Shared company scope avoids concurrent discoveries of the same URL via
    # two different entry points. Other companies remain independent.
    with document_lock("scan-company-" + company_id):
        url = normalize_url(watch["source_url"])
        mode = effective_mode(watch)
        new, known, unchanged, warnings = 0, 0, 0, []
        if mode == "SINGLE_PAGE":
            # Lire est nécessaire pour constater une modification. Cette capture
            # temporaire n'entre dans le stock qu'après sélection explicite.
            metadata, snapshot = _capture(watch, url)
            previous = _last_observation(company_id, url)
            baseline = (previous.get("CONTENT_SHA256") if previous else None) or _legacy_hash(company_id, metadata["url"])
            if baseline and baseline == metadata["content_sha256"]:
                if previous:
                    if previous.get("CONTENT_SHA256"):
                        _touch(previous["ID_DISCOVERY"])
                    else:
                        _bind_first_observation(previous, metadata, snapshot)
                unchanged = 1
            elif previous and not baseline:
                _bind_first_observation(previous, metadata, snapshot)
                known = 1
            else:
                _insert_candidate(watch, url, metadata["title"], "UPDATED_PAGE" if baseline else "NEW_PAGE",
                                  content_hash=metadata["content_sha256"], snapshot=snapshot)
                new = 1
            warnings = ["Comparaison du texte utile de cette page uniquement ; régler content_selector pour une zone stable."]
        else:
            result = discover({**watch, "collection_config": {**(watch.get("collection_config") or {}), "mode": "LISTING"}})
            warnings = result.get("warnings") or []
            # Ne lire ni capturer les articles au stade de la découverte d'URL.
            existing = _query(f"SELECT URL FROM `{DISCOVERY}` WHERE ID_COMPANY=@company",
                              [_p("company", "STRING", company_id)])
            legacy = _query(f"SELECT SOURCE_URL FROM `{DOCUMENT}` WHERE ID_COMPANY=@company AND ID_COMPANY_WATCH IS NOT NULL",
                            [_p("company", "STRING", company_id)])
            urls = _known_keys(existing, "URL") | _known_keys(legacy, "SOURCE_URL")
            pending = []
            for item in result["items"]:
                target = normalize_url(item["url"])
                key = url_key(target)
                if key in urls:
                    known += 1
                    continue
                pending.append({"url": target, "title": item.get("title")})
                urls.add(key)
            new = _insert_candidates_batch(watch, pending)
        return {"status": "ok", "new": new, "known": known, "unchanged": unchanged, "warnings": warnings}


def _candidate_out(row):
    item = {k.lower(): v for k, v in dict(row).items()}
    item["library_status"] = item.get("library_status") or "PENDING"
    item["published_at"] = None
    item["publication_date_note"] = None
    snapshot = item.get("snapshot_uri")
    if not snapshot:
        return item
    try:
        metadata = json.loads(_read_uri(snapshot))
        date = metadata.get("published_at")
        if date:
            parsed = datetime.fromisoformat(str(date).replace("Z", "+00:00"))
            # A timestamp without a timezone must not be assigned an invented zone.
            if parsed.tzinfo is not None:
                item["published_at"] = parsed.astimezone(timezone.utc).isoformat()
        if metadata.get("provider") == "BRIGHTDATA":
            item["publication_date_note"] = "Date du post retournée par LinkedIn ; pour un relais, la date de partage n’est pas établie."
    except Exception:
        # Missing/corrupt storage must not hide the selection table or invent a date.
        logger.warning("[CORPO LIST] publication date unavailable for discovery=%s", item.get("id_discovery"))
        item["publication_date_note"] = "Date indisponible : les métadonnées de capture n’ont pas pu être lues."
    return item


def list_candidates(company_id=None, watch_id=None, status="NEW", offset=0, limit=50):
    if status not in {"NEW", "STORED", "DISMISSED", "ALL", "IMPORTING", "IMPORTED", "ERROR"}:
        raise ValueError("Statut invalide")
    clauses, params = [], []
    if company_id:
        clauses.append("d.ID_COMPANY=@company"); params.append(_p("company", "STRING", company_id))
    if watch_id:
        clauses.append("d.ID_COMPANY_WATCH=@watch"); params.append(_p("watch", "STRING", watch_id))
    if status == "NEW":
        clauses.append("d.STATUS IN ('NEW','STORED') AND COALESCE(d.LIBRARY_STATUS,'PENDING')='PENDING'")
    elif status in {"IMPORTING", "IMPORTED", "ERROR"}:
        clauses.append("d.LIBRARY_STATUS=@status"); params.append(_p("status", "STRING", status))
    elif status != "ALL":
        clauses.append("d.STATUS=@status"); params.append(_p("status", "STRING", status))
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    params += [_p("limit", "INT64", limit + 1), _p("offset", "INT64", offset)]
    rows = _query(f"""SELECT d.*, w.LABEL AS WATCH_LABEL, c.NAME AS COMPANY_NAME,
        w.IS_ACTIVE AS WATCH_ACTIVE, w.COLLECTION_METHOD
        FROM `{DISCOVERY}` d LEFT JOIN `{WATCH}` w USING (ID_COMPANY_WATCH, ID_COMPANY)
        LEFT JOIN `{COMPANY}` c ON c.ID_COMPANY=d.ID_COMPANY {where}
        ORDER BY d.DATE_FOUND DESC, d.ID_DISCOVERY DESC LIMIT @limit OFFSET @offset""", params)
    # Only this page's existing GCS metadata; never fetch LinkedIn or query BQ per row.
    with ThreadPoolExecutor(max_workers=8) as pool:
        items = list(pool.map(_candidate_out, rows[:limit]))
    return {"items": items, "has_more": len(rows)>limit, "offset": offset, "limit": limit}


def get_candidate(candidate_id):
    rows = _query(f"SELECT * FROM `{DISCOVERY}` WHERE ID_DISCOVERY=@id LIMIT 1",
                  [_p("id", "STRING", candidate_id)])
    if not rows:
        raise HTTPException(404, "URL découverte introuvable")
    return dict(rows[0])


def change_candidates_status(discovery_ids, action):
    """One conditional DML job for the selection, never one job per URL."""
    if not isinstance(discovery_ids, list) or not 1 <= len(discovery_ids) <= 500:
        raise ValueError("Sélection attendue : entre 1 et 500 identifiants")
    if any(not isinstance(value, str) or not value.strip() for value in discovery_ids):
        raise ValueError("Identifiant de découverte invalide")
    ids = list(dict.fromkeys(value.strip() for value in discovery_ids))
    transitions = {"DISMISS": ("NEW", "DISMISSED"), "RESTORE": ("DISMISSED", "NEW")}
    if action not in transitions:
        raise ValueError("Action invalide")
    before, after = transitions[action]
    rows = _query(f"""UPDATE `{DISCOVERY}` SET STATUS=@after,
        ERROR=NULL, UPDATED_AT=CURRENT_TIMESTAMP()
        WHERE ID_DISCOVERY IN UNNEST(@ids) AND STATUS=@before
          AND COALESCE(LIBRARY_STATUS,'PENDING') IN ('PENDING','ERROR')
          AND (@after='NEW' OR ID_DOCUMENT IS NULL);
        SELECT @@row_count AS UPDATED_COUNT;""",
        [bigquery.ArrayQueryParameter("ids", "STRING", ids),
         _p("before", "STRING", before), _p("after", "STRING", after)])
    updated = int(rows[0]["UPDATED_COUNT"])
    return {"status": "ok", "requested": len(ids), "updated": updated, "skipped": len(ids)-updated}


def store_candidate(candidate_id):
    with document_lock("stock-" + candidate_id):
        candidate = get_candidate(candidate_id)
        if candidate["STATUS"] == "STORED":
            return {"status": "STORED", "id_stock": candidate["ID_STOCK"], "already_exists": True}
        if candidate["STATUS"] != "NEW":
            raise HTTPException(409, "Cette URL n'est pas disponible pour stockage")
        watch = active_watch(candidate["ID_COMPANY"], candidate["ID_COMPANY_WATCH"])
        if watch["collection_method"] not in {"HTML", "BRIGHTDATA"}:
            raise HTTPException(409, "Ce point n'est plus configuré pour une collecte automatique")
        try:
            if candidate.get("SNAPSHOT_URI"):
                metadata_uri = candidate["SNAPSHOT_URI"]
                metadata = json.loads(_read_uri(metadata_uri))
            else:
                if watch["collection_method"] == "BRIGHTDATA":
                    raise HTTPException(409, "Capture Bright Data absente ; aucun repli HTML vers LinkedIn")
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
                ASSERT (SELECT COUNT(*) FROM `{DISCOVERY}`
                  WHERE ID_DISCOVERY=@discovery AND STATUS='NEW') = 1
                  AS 'Cette URL a changé de statut ; actualiser la liste';
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
            "captured_at": metadata["captured_at"], "text": _read_uri(metadata["text_storage_uri"]),
            "published_at": metadata.get("published_at"), "author_name": metadata.get("author_name"),
            "author_id": metadata.get("author_id"), "monitored_account_url": metadata.get("monitored_account_url"),
            "repost": metadata.get("repost"), "share_date": metadata.get("share_date")}
