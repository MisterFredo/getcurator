"""Cockpit job for the existing employee-post requalification rules."""

import hashlib
import logging
import time
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import HTTPException

from core.company import library_post_requalify as requalify
from core.company import watch_monitoring as state
from core.library.company_watch_library import document_lock

logger = logging.getLogger(__name__)
PATH = "library-post-requalification.json"
LOCK = "post-requalification-" + hashlib.sha256(state.ROOT.encode()).hexdigest()
BATCH_SIZE = 5
STALE_AFTER = timedelta(minutes=15)


def _public(job):
    result = {key: value for key, value in job.items() if key != "deferred_ids"}
    if result["status"] == "RUNNING":
        age = datetime.now(timezone.utc) - datetime.fromisoformat(job["updated_at"])
        if age >= STALE_AFTER:
            result.update(status="PARTIAL", error="Traitement interrompu. Vous pouvez reprendre.")
    return result


def _save(job):
    job["updated_at"] = state.stamp()
    state.save(PATH, job)


def status():
    job = state.load(PATH)
    if job is None:
        return {"status": "IDLE", "remaining": requalify.count_candidates()}
    return _public(job)


def launch(background_tasks):
    with document_lock(LOCK + "-start"):
        previous = state.load(PATH)
        if previous and _public(previous)["status"] == "RUNNING":
            return _public(previous)

        with document_lock(LOCK + "-batch"):
            remaining = requalify.count_candidates()
            job = {
                "id_job": str(uuid4()),
                "status": "RUNNING" if remaining else "COMPLETE",
                "remaining": remaining,
                "written": 0,
                "skipped": 0,
                "failed": 0,
                "deferred_ids": [],
            }
            _save(job)
            if remaining:
                background_tasks.add_task(run, job["id_job"])
            return _public(job)


def run(job_id):
    while True:
        try:
            with document_lock(LOCK + "-batch"):
                job = state.load(PATH)
                if not job or job["id_job"] != job_id or job["status"] != "RUNNING":
                    return

                try:
                    rows = requalify._candidates(BATCH_SIZE, excluded_ids=job["deferred_ids"])
                    if not rows:
                        job["remaining"] = requalify.count_candidates()
                        job["status"] = "PARTIAL" if job["remaining"] else "COMPLETE"
                    for row in rows:
                        _process(job, row)
                        _save(job)
                except Exception:
                    logger.exception("Requalification Cockpit interrompue")
                    job.update(status="PARTIAL", error="Traitement interrompu. Consultez les logs backend.")
                _save(job)

                if job["status"] != "RUNNING":
                    return
        except HTTPException as exc:
            if exc.status_code != 409:
                raise
            return
        time.sleep(1)


def _process(job, row):
    try:
        _, written = requalify.apply_candidate(row)
    except Exception:
        logger.exception("Requalification impossible pour %s", row["ID_DOCUMENT"])
        job["deferred_ids"].append(row["ID_DOCUMENT"])
        job["failed"] += 1
    else:
        job["written" if written else "skipped"] += 1
        if not written:
            job["deferred_ids"].append(row["ID_DOCUMENT"])
        job["remaining"] = max(0, job["remaining"] - 1)
