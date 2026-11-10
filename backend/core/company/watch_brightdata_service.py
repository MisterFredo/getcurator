"""Durable, resumable Corpo jobs. Provider runs remotely; ingestion resumes on demand."""
from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from google.api_core.exceptions import NotFound
from utils.gcs import bucket
from core.discovery import brightdata_linkedin as provider
from core.library.company_watch_library import _upload, _read_uri, document_lock


logger = logging.getLogger(__name__)

def _provider_failure(state, exc):
    state["provider_error"] = provider.error_diagnostic(exc)
    logger.warning("[CORPO BRIGHTDATA] %s", provider.safe_error_text(exc))


def _state_path(company, watch):
    # Hash user-controlled IDs before using them as object names.
    key = hashlib.sha256(json.dumps([company, watch]).encode()).hexdigest()
    return f"company-watch/brightdata/jobs/{key}.json"


def _load(company, watch):
    try:
        return json.loads(bucket.blob(_state_path(company, watch)).download_as_text())
    except NotFound:
        return None


def _save(company, watch, state):
    # All calls occur inside the same distributed company lease as HTML discovery.
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    bucket.blob(_state_path(company, watch)).upload_from_string(
        json.dumps(state, ensure_ascii=False), content_type="application/json")


def _response(state):
    return {"status": state["status"], "snapshot_id": state.get("snapshot_id"),
        "new": state.get("new", 0), "known": state.get("known", 0), "unchanged": 0,
        "warnings": state.get("warnings", []), "received": state.get("received", 0),
        "message": state.get("message"), "provider_error": state.get("provider_error"), "retry_after_seconds": 10}


def scan_linkedin(company_id, watch_id, *, start=False):
    # Lazy import prevents a cycle and keeps the transport reusable by Media.
    from core.company.watch_discovery_service import active_watch
    watch = active_watch(company_id, watch_id)
    with document_lock("scan-company-" + company_id):
        state = _load(company_id, watch_id)
        pending = state and state["status"] in {"STARTING", "RUNNING", "UNKNOWN"}
        if start and not pending:
            if watch["collection_method"] != "BRIGHTDATA":
                raise ValueError("Ce point n'est pas configuré en Bright Data")
            provider.validate_config(watch["source_url"], watch.get("collection_config") or {})
            try:
                provider._token()
            except provider.ProviderError as exc:
                raise HTTPException(503, str(exc)) from None
            frozen = {key: watch.get(key) for key in ("id_company", "id_company_watch", "company_name",
                "label", "source_url", "source_type", "source_role", "author_name", "collection_method", "collection_config")}
            state = {"status": "STARTING", "watch": frozen,
                "run_id": uuid.uuid4().hex, "started_at": datetime.now(timezone.utc).isoformat()}
            _save(company_id, watch_id, state)  # Save intent before external side effect.
            try:
                state["snapshot_id"] = provider.trigger(watch["source_url"], watch.get("collection_config") or {})
            except provider.AmbiguousTrigger as exc:
                _provider_failure(state, exc)
                state.update(status="UNKNOWN", message="Lancement incertain — " + str(exc) + ". Vérifier la collecte dans Bright Data avant de la rattacher ici. Aucun nouveau lancement automatique.")
                _save(company_id, watch_id, state)
                return _response(state)
            except provider.ProviderError as exc:
                _provider_failure(state, exc)
                state.update(status="FAILED", message="Échec du lancement — " + str(exc))
                _save(company_id, watch_id, state)
                raise HTTPException(502, state["message"]) from None
            state["status"] = "RUNNING"
            _save(company_id, watch_id, state)
            return _response(state)
        if not state:
            return {"status": "IDLE", "new": 0, "known": 0, "unchanged": 0, "warnings": []}
        if state["status"] in {"STARTING", "UNKNOWN"}:
            # Includes backend crash after trigger but before snapshot ID write.
            return {**_response(state), "status": "UNKNOWN",
                "message": state.get("message") or "Lancement incertain. Rattacher l'identifiant de collecte depuis la console Bright Data pour reprendre sans nouvel achat."}
        if state["status"] != "RUNNING":
            return _response(state)
        try:
            status = provider.progress(state["snapshot_id"])
            # Clear a prior temporary read error after a successful provider reply.
            if state.get("provider_error"):
                state.update(provider_error=None, message=None)
                _save(company_id, watch_id, state)
            if status in {"failed", "canceled"}:
                state.update(status="FAILED", message="La collecte Bright Data a échoué ou a été annulée ; vérifier sa console.")
                _save(company_id, watch_id, state)
                return _response(state)
            if status != "ready":
                return _response(state)
            if state.get("result_uri"):
                records = json.loads(_read_uri(state["result_uri"]))
            else:
                records = provider.download(state["snapshot_id"])
                state["result_uri"] = _upload(f"company-watch/brightdata/results/{state['run_id']}.json",
                    json.dumps(records, ensure_ascii=False).encode(), "application/json")
                _save(company_id, watch_id, state)
            _ingest(company_id, watch_id, state, records)
        except provider.ProviderError as exc:
            # Keep RUNNING and the snapshot ID: subsequent calls only recover it.
            _provider_failure(state, exc)
            state["message"] = "Échec de récupération — " + str(exc)
            _save(company_id, watch_id, state)
            raise HTTPException(502, state["message"]) from None
        return _response(state)


def attach_snapshot(company_id, watch_id, snapshot_id):
    """Recover an ambiguous paid launch using its ID from the vendor console."""
    from core.company.watch_discovery_service import active_watch
    active_watch(company_id, watch_id)
    snapshot_id = provider._snapshot(snapshot_id)
    with document_lock("scan-company-" + company_id):
        state = _load(company_id, watch_id)
        if not state or state["status"] not in {"STARTING", "UNKNOWN"}:
            raise HTTPException(409, "Le rattachement est réservé à un lancement incertain")
        # Validate the ID against the provider before accepting it. No paid launch.
        try:
            provider.progress(snapshot_id)
        except provider.ProviderError as exc:
            raise HTTPException(502, str(exc)) from None
        state.update(snapshot_id=snapshot_id, status="RUNNING", message=None, provider_error=None)
        _save(company_id, watch_id, state)
        return _response(state)


def _ingest(company_id, watch_id, state, records):
    from core.company import watch_discovery_service as discovery
    watch = state["watch"]
    expected = provider.account_url(watch["source_url"])[0]
    valid_records, failures = [], []
    for record in records:
        if isinstance(record, dict) and (record.get("error") or record.get("error_code")):
            failures.append({key: provider.safe_error_text(record[key]) for key in ("error", "error_code")
                             if record.get(key) is not None})
            continue
        # Actual publications still require matching provenance. Do not accept an
        # input URL as proof for a publication belonging to another account.
        origin = (record.get("discovery_input") or {}) if isinstance(record, dict) else {}
        origin = origin.get("url") if isinstance(origin, dict) else None
        try:
            matches = origin and provider.account_url(origin)[0] == expected
        except ValueError:
            matches = False
        if not matches:
            state.update(status="FAILED", message="Origine d’une publication non correspondante : aucun post importé.",
                         provider_error={"phase":"provenance","message":"Origine d’une publication non correspondante"})
            _save(company_id, watch_id, state)
            return
        valid_records.append(record)
    if failures:
        state["record_errors"] = failures
        state["record_errors_uri"] = _upload(f"company-watch/brightdata/results/{state['run_id']}-provider-errors.json",
            json.dumps(failures, ensure_ascii=False).encode(), "application/json")
    if records and not valid_records:
        detail = " | ".join(dict.fromkeys((row.get("error_code", "") + " : " + row.get("error", "")).strip(" :") for row in failures))
        state.update(status="FAILED", received=len(records), new=0, known=0,
                     message="Aucune publication récupérée — Bright Data : " + provider.safe_error_text(detail),
                     provider_error={"phase":"result_records","message":provider.safe_error_text(detail)})
        _save(company_id, watch_id, state)
        return
    posts, issues = provider.normalize_records(valid_records)
    existing = discovery._query(f"SELECT URL FROM `{discovery.DISCOVERY}` WHERE ID_COMPANY=@company",
        [discovery._p("company", "STRING", company_id)])
    legacy = discovery._query(f"SELECT SOURCE_URL FROM `{discovery.DOCUMENT}` WHERE ID_COMPANY=@company AND ID_COMPANY_WATCH IS NOT NULL",
        [discovery._p("company", "STRING", company_id)])
    known_ids = {identifier for r in existing + legacy
        if (identifier := provider.post_id(r.get("URL") or r.get("SOURCE_URL")))}
    items, known = [], 0
    for post in posts:
        if post["post_id"] in known_ids:
            known += 1; continue
        metadata, uri = _cache_post(watch, post, state)
        items.append({"url": post["url"], "title": metadata["title"],
            "content_hash": metadata["content_sha256"], "snapshot": uri})
        known_ids.add(post["post_id"])
    count = discovery._insert_candidates_batch(watch, items, batch_id=state["run_id"])
    warnings = ["La collecte ne garantit pas l'exhaustivité. Pour les contenus relayés, la date reçue peut être celle du post original ; elle ne prouve pas la date du relais."]
    if failures:
        warnings.append(f"{len(failures)} ligne(s) d’erreur fournisseur isolée(s) ; les publications valides ont été conservées.")
    if issues:
        issues_uri = _upload(f"company-watch/brightdata/results/{state['run_id']}-issues.json",
            json.dumps(issues).encode(), "application/json")
        state["issues_uri"] = issues_uri
        warnings.append(f"{len(issues)} anomalie(s) conservée(s) dans l'audit de collecte ; les lignes sans texte ou identifiant valide ne sont pas importées.")
    limit = provider.validate_config(watch["source_url"], watch.get("collection_config") or {})
    if limit is not None and len(records) >= limit:
        warnings.append(f"Plafond de {limit} résultats atteint : la couverture peut être partielle.")
    # Empty/error-only output must not masquerade as a successful scan.
    state.update(status="COMPLETE" if posts or not records else "FAILED", new=count, known=known,
        received=len(records), warnings=warnings,
        message=None if posts or not records else "Aucune publication exploitable dans la réponse ; consulter l'audit Bright Data.")
    _save(company_id, watch_id, state)


def _cache_post(watch, post, state):
    raw = json.dumps(post["raw"], ensure_ascii=False).encode()
    text = post["text"].encode()
    raw_hash, text_hash = hashlib.sha256(raw).hexdigest(), hashlib.sha256(text).hexdigest()
    path = f"company-watch/brightdata/captures/{watch['id_company_watch']}/{post['post_id']}/{raw_hash}"
    title = " ".join(post["text"].split())[:200]
    metadata = {"url": post["url"], "requested_url": post["original_url"], "title": title,
        "published_at": post["published_at"], "date_precision": "EXACT" if post["published_at"] else "UNKNOWN",
        "captured_at": datetime.now(timezone.utc).isoformat(), "original_sha256": raw_hash,
        "content_sha256": text_hash, "storage_uri": _upload(path + "/original.json", raw, "application/json"),
        "text_storage_uri": _upload(path + "/text.txt", text, "text/plain; charset=utf-8"),
        "id_company": watch["id_company"], "id_company_watch": watch["id_company_watch"],
        "source_role": watch["source_role"], "provider": "BRIGHTDATA", "post_id": post["post_id"],
        "author_name": post["author_name"], "author_id": post["author_id"], "author_url": post["author_url"],
        "monitored_account_url": watch["source_url"], "monitored_person_name": watch.get("author_name"),
        "repost": post["repost"], "share_date": None,
        "snapshot_id": state["snapshot_id"], "collection_config": watch.get("collection_config") or {}}
    uri = _upload(path + "/" + state["run_id"] + ".json",
        json.dumps(metadata, ensure_ascii=False).encode(), "application/json")
    return metadata, uri
