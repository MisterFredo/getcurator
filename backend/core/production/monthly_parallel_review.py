"""Parallel page reviews under ONE durable Production lock.

Each child is marked SUBMITTING before its HTTP call. Acceptance IDs are saved
before parsing. A crash/transport ambiguity never causes an automatic resend.
Only the parent writes the shared batch state; child callbacks serialize writes.
"""
import copy
import json
import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid5

from config import BQ_DATASET, BQ_PROJECT
from core.production import workflow_repository as repo, workflow_service as workflow
from core.production.document_service import client, load_corpus
from core.production.monthly_audit_service import (
    _hash, _serialize, audit_requests, AUDIT_WORKFLOW, PAGE_INSTRUCTIONS, CROSS_INSTRUCTIONS,
)
from core.production.monthly_models import MonthlyQualityReview
from core.production.monthly_repair_rules import AUDIT_REVISION
from core.production.monthly_review import deterministic_issues
from core.production import monthly_state as state
from core.production.monthly_parallel_repository import save_batch
from core.production.monthly_runtime import review_payload
from utils.bigquery_utils import query_bq

logger = logging.getLogger(__name__)
BATCH_KIND = "MONTHLY_PARALLEL_REVIEW_V1"
BATCH_STAGE = "REVIEW_BATCH"
PER_REPORT = 10
GLOBAL_IN_FLIGHT = 20  # Per API process; deployment currently has one worker.
_POOL = ThreadPoolExecutor(max_workers=GLOBAL_IN_FLIGHT, thread_name_prefix="monthly-review")
_CAPACITY_LOCK = threading.Lock()
_CLAIMED = set()
_HYDRATED = False
_LOCKS_GUARD = threading.Lock()
_LOCKS = {}
TERMINAL_ERRORS = {"failed", "validation_failed", "incomplete", "cancelled"}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _hydrate():
    global _HYDRATED
    with _CAPACITY_LOCK:
        if _HYDRATED:
            return
        rows = query_bq(f"""
            SELECT ARTIFACT_ID, TO_JSON_STRING(RESULT_JSON) AS RESULT
            FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_PRODUCTION_ARTIFACT`
            WHERE STAGE='REVIEW_BATCH'
              AND STATUS IN ('STARTING','SUBMISSION_UNKNOWN','queued','in_progress')
        """) or []
        for row in rows:
            result = json.loads(row["RESULT"]) if isinstance(row["RESULT"], str) else row["RESULT"]
            for key, child in (result or {}).get("checks", {}).items():
                if child["status"] in {"SUBMITTING", "SUBMISSION_UNKNOWN", "queued", "in_progress"}:
                    _CLAIMED.add((row["ARTIFACT_ID"], key))
        _HYDRATED = True


def _claim(artifact_id, key):
    with _CAPACITY_LOCK:
        token = (artifact_id, key)
        if token in _CLAIMED:
            return True
        if len(_CLAIMED) >= GLOBAL_IN_FLIGHT:
            return False
        _CLAIMED.add(token)
        return True


def _release(artifact_id, key):
    with _CAPACITY_LOCK:
        _CLAIMED.discard((artifact_id, key))


def _lock(artifact_id):
    with _LOCKS_GUARD:
        return _LOCKS.setdefault(artifact_id, threading.Lock())


def _request_key(stage, payload):
    # Same key as v1: already checked, unchanged pages remain reusable.
    return _hash({"revision": AUDIT_REVISION, "stage": stage, "payload": payload})


def _derive(job):
    checks = list(job["checks"].values())
    known_active = any(c["status"] in {"SUBMITTING", "queued", "in_progress"} for c in checks)
    errors = [c for c in checks if c["status"] in TERMINAL_ERRORS]
    if errors:
        for child in checks:
            if child["status"] == "pending":
                child.update(status="cancelled", error={"message": "Contrôle non envoyé après un échec technique."})
    unknown = any(c["status"] == "SUBMISSION_UNKNOWN" for c in checks)
    if known_active:
        job["status"] = "in_progress"
    elif unknown:
        job["status"] = "SUBMISSION_UNKNOWN"
        job["error"] = {"message": "Une acceptation de contrôle reste inconnue. Rattachez sa réponse avant de reprendre."}
    elif errors:
        job["status"] = "failed"
        job["error"] = errors[0].get("error") or {"message": "Un contrôle n’a pas abouti."}
    elif any(c["status"] == "pending" for c in checks):
        job["status"] = "queued"
    else:
        issues = list(job.get("deterministic_issues") or [])
        seen = {_hash(issue) for issue in issues}
        for child in checks:
            for issue in child["review"]["issues"]:
                key = _hash(issue)
                if key not in seen:
                    seen.add(key)
                    issues.append(issue)
        job.update(status="completed", review={"passed": not issues, "issues": issues}, error=None)
    return job


def _persist(item, job):
    job["updated_at"] = _now()
    item = save_batch(item, _derive(job))
    state.remember(item)
    return item


def _merge(job, key, result):
    child = job["checks"][key]
    values = {"status": result["status"], "response_id": result.get("id") or child.get("response_id")}
    for field in ("model", "review", "error", "usage"):
        if field in result and (result[field] is not None or field == "error"):
            values[field] = result[field]
    changed = any(child.get(k) != v for k, v in values.items())
    if changed:
        child.update(values, updated_at=_now())
    return changed


def _metadata(item, key):
    return {"workflow": AUDIT_WORKFLOW, "production_id": item["production_id"],
            "corpus_sha256": item["corpus_sha256"], "artifact_id": item["artifact_id"],
            "input_sha256": key}


def _retrieve(item, key, response_id):
    with client() as connection:
        response = connection.responses.retrieve(response_id)
    if any((response.metadata or {}).get(k) != v for k, v in _metadata(item, key).items()):
        raise ValueError("La réponse ne correspond pas à ce contrôle et à son socle.")
    check = item["request"]["checks"][key]
    return _serialize(response, check)


def _submit_pending(item, job):
    artifact_id, production_id = item["artifact_id"], item["production_id"]
    if any(c["status"] == "SUBMISSION_UNKNOWN" for c in job["checks"].values()):
        return item
    if any(c["status"] in TERMINAL_ERRORS for c in job["checks"].values()):
        for child in job["checks"].values():
            if child["status"] == "pending":
                child.update(status="cancelled", error={"message": "Contrôle non envoyé après l’échec d’un autre contrôle."})
        return _persist(item, job)
    running = sum(c["status"] in {"queued", "in_progress"} for c in job["checks"].values())
    selected = []
    for key, child in job["checks"].items():
        if child["status"] == "pending" and running + len(selected) < PER_REPORT and _claim(artifact_id, key):
            selected.append(key)
    if not selected:
        return item
    # One write reserves this entire wave before any external submission.
    for key in selected:
        job["checks"][key].update(status="SUBMITTING", started_at=_now())
    try:
        item = _persist(item, job)
    except Exception:
        for key in selected:
            _release(artifact_id, key)
        raise
    writer = threading.Lock()
    merge_guard = threading.Lock()
    acknowledged_ids = set()

    def accept(response, key):
        # Merge IDs immediately even while another callback waits on BQ.
        # The next writer flushes all accumulated IDs in one CAS write.
        # Each callback still waits until its own ID is durable before parsing.
        with merge_guard:
            _merge(job, key, {"status": "queued", "id": response.id, "model": response.model})
        with writer:
            if response.id in acknowledged_ids:
                return
            with merge_guard:
                snapshot = copy.deepcopy(job)
            _persist(item, snapshot)
            with merge_guard:
                job["write_revision"] = snapshot["write_revision"]
                job["updated_at"] = snapshot["updated_at"]
                acknowledged_ids.update(c["response_id"] for c in snapshot["checks"].values() if c.get("response_id"))

    def submit(key):
        check = item["request"]["checks"][key]
        schema = MonthlyQualityReview.model_json_schema()
        if "locations" in check["payload"]:
            schema["$defs"]["MonthlyReviewIssue"]["properties"]["location"] = {
                "type": "string", "enum": check["payload"]["locations"],
            }
        try:
            with client() as connection:
                response = connection.responses.create(
                    model=os.getenv("PRODUCTION_REVIEW_MODEL") or os.getenv("PRODUCTION_DOCUMENT_MODEL") or "gpt-5.4",
                    instructions=PAGE_INSTRUCTIONS if check["stage"] == "REVIEW_PAGE" else CROSS_INSTRUCTIONS,
                    input=json.dumps(review_payload(check["payload"]), ensure_ascii=False, allow_nan=False),
                    text={"format": {"type": "json_schema", "name": "monthly_page_review", "strict": True, "schema": schema}},
                    reasoning={"effort": "low"}, max_output_tokens=8000,
                    background=True, store=True, metadata=_metadata(item, key),
                )
            logger.info("Monthly review accepted production=%s artifact=%s check=%s response=%s",
                        production_id, artifact_id, key, response.id)
            accept(response, key)
            return key, _serialize(response, check)
        except Exception as exc:
            logger.exception("Monthly review submission interrupted check=%s", key)
            with merge_guard:
                saved_id = job["checks"][key].get("response_id")
            if saved_id:
                return key, {"status": "queued", "id": saved_id}
            definite = isinstance(exc, workflow.APIStatusError) and 400 <= exc.status_code < 500 and exc.status_code != 408
            return key, {"status": "failed" if definite else "SUBMISSION_UNKNOWN",
                         "error": {"message": str(exc)[:1500]}}

    futures = [_POOL.submit(submit, key) for key in selected]
    changed = False
    for future in futures:
        key, result = future.result()
        changed |= _merge(job, key, result)
        if result["status"] in TERMINAL_ERRORS | {"completed"}:
            _release(artifact_id, key)
    # Flush once after all callbacks, including any accepted ID whose first
    # save encountered a transient DB failure. Never resubmit that child.
    return _persist(item, job)


def start_parallel_review(production_id, artifact_id, document_id):
    _hydrate()
    with _lock(artifact_id):
        existing = state.get_artifact(production_id, artifact_id)
        if existing:
            return existing
        corpus = load_corpus(production_id)
        parent = state.get_artifact(production_id, document_id)
        if (not parent or parent["stage"] != "DOCUMENT" or parent["status"] != "completed"
                or parent["corpus_sha256"] != corpus.corpus_sha256):
            raise ValueError("Document complet correspondant au socle requis.")
        document = parent["result"]["document"]
        checks = {}
        for stage, payload in audit_requests(document, corpus):
            key = _request_key(stage, payload)
            checks[key] = {"stage": stage, "payload": payload, "input_sha256": key}
        cached = {}
        for old in state.history(production_id):
            result = old.get("result") or {}
            if old["corpus_sha256"] != corpus.corpus_sha256:
                continue
            if old["stage"] in {"REVIEW_PAGE", "REVIEW_CROSS"} and old["status"] == "completed":
                key = (old.get("request") or {}).get("input_sha256")
                if key in checks:
                    cached.setdefault(key, {"status": "completed", "review": result["review"], "cached": True})
            for key, child in result.get("checks", {}).items():
                if key in checks and child["status"] == "completed":
                    cached.setdefault(key, {**copy.deepcopy(child), "cached": True})
        request = {"kind": BATCH_KIND, "audit_revision": AUDIT_REVISION,
                   "document_artifact_id": document_id, "checks": checks}
        job = {"status": "queued", "kind": BATCH_KIND, "audit_revision": AUDIT_REVISION,
               "document_artifact_id": document_id, "started_at": _now(),
               "deterministic_issues": deterministic_issues(document, corpus),
               "checks": {key: cached.get(key) or {"status": "pending", "response_id": None} for key in checks}}
        item, created = workflow._reserve(production_id=production_id, artifact_id=artifact_id,
            stage=BATCH_STAGE, corpus_sha256=corpus.corpus_sha256, request=request, parent_id=document_id)
        if not created:
            return item
        item = _persist(item, job)
        if item["status"] in repo.ACTIVE:
            return _submit_pending(item, job)
        return item


def refresh_parallel_review(production_id, artifact_id, response_id=None):
    _hydrate()
    with _lock(artifact_id):
        item = repo.get_artifact(production_id, artifact_id)
        if not item or item["stage"] != BATCH_STAGE or item["request"].get("kind") != BATCH_KIND:
            raise ValueError("Lot de contrôles introuvable.")
        if item["status"] not in repo.ACTIVE:
            return item
        job = copy.deepcopy(item.get("result") or {})
        if not job:
            # Reservation was durable, but the initial state write never
            # happened. No child can have been sent before that first write.
            corpus = load_corpus(production_id)
            parent = state.get_artifact(production_id, item["request"]["document_artifact_id"])
            if not parent or parent["corpus_sha256"] != item["corpus_sha256"]:
                raise ValueError("Document source du lot introuvable ou incohérent.")
            job = {"status": "queued", "kind": BATCH_KIND, "audit_revision": AUDIT_REVISION,
                   "document_artifact_id": parent["artifact_id"], "started_at": _now(),
                   "deterministic_issues": deterministic_issues(parent["result"]["document"], corpus),
                   "checks": {key: {"status": "pending", "response_id": None} for key in item["request"]["checks"]}}
            item = _persist(item, job)
        changed = False
        if response_id:
            with client() as connection:
                response = connection.responses.retrieve(response_id)
            key = (response.metadata or {}).get("input_sha256")
            if key not in job["checks"] or any((response.metadata or {}).get(k) != v for k, v in _metadata(item, key).items()):
                raise ValueError("Cette réponse ne correspond pas à un contrôle de ce lot.")
            child = job["checks"][key]
            if child.get("response_id") and child["response_id"] != response_id:
                raise ValueError("Ce contrôle est rattaché à une autre réponse.")
            changed |= _merge(job, key, _serialize(response, item["request"]["checks"][key]))
            if job["checks"][key]["status"] in TERMINAL_ERRORS | {"completed"}:
                _release(artifact_id, key)
        # SUBMITTING with no saved ID after restart is uncertain, never pending.
        for child in job["checks"].values():
            if child["status"] == "SUBMITTING" and not child.get("response_id"):
                child["status"] = "SUBMISSION_UNKNOWN"
                changed = True
        pending = [(key, c["response_id"]) for key, c in job["checks"].items()
                   if c.get("response_id") and c["status"] in {"queued", "in_progress", "SUBMISSION_UNKNOWN"}]
        futures = [(key, _POOL.submit(_retrieve, item, key, rid)) for key, rid in pending]
        for key, future in futures:
            try:
                result = future.result()
                changed |= _merge(job, key, result)
                if result["status"] in TERMINAL_ERRORS | {"completed"}:
                    _release(artifact_id, key)
            except Exception:
                logger.exception("Monthly review poll failed; retained response check=%s", key)
        if changed:
            item = _persist(item, job)
        if item["status"] in repo.ACTIVE:
            return _submit_pending(item, job)
        return item


def progress(item):
    if not item or item["stage"] != BATCH_STAGE:
        return None
    result = item.get("result") or {}
    checks = result.get("checks") or {}
    pages = [checks[key] for key, spec in item["request"]["checks"].items() if spec["stage"] == "REVIEW_PAGE" and key in checks]
    cross = [checks[key] for key, spec in item["request"]["checks"].items() if spec["stage"] == "REVIEW_CROSS" and key in checks]
    return {"pages_total": len(pages), "pages_completed": sum(c["status"] == "completed" for c in pages),
            "pages_reused": sum(c.get("cached", False) for c in pages),
            "checks_running": sum(c["status"] in {"queued", "in_progress", "SUBMITTING"} for c in checks.values()),
            "checks_waiting": sum(c["status"] == "pending" for c in checks.values()),
            "cross_status": cross[0]["status"] if cross else "pending",
            "started_at": result.get("started_at"), "updated_at": result.get("updated_at"),
            "finished_at": result.get("updated_at") if item["status"] in TERMINAL_ERRORS | {"completed"} else None}
