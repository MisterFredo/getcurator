"""Explicit, resumable registration and qualification from the Cockpit."""

import hashlib
import logging
from uuid import uuid4

from fastapi import HTTPException

from core.company import watch_monitoring as state
from core.library.company_watch_library import document_lock

logger = logging.getLogger(__name__)
PATH = "library-post-backlog.json"
LOCK = "library-post-backlog-" + hashlib.sha256(state.ROOT.encode()).hexdigest()
BATCH_SIZE = 20
IMPORT_BATCH_SIZE = 100


def status():
    job = state.load(PATH, {"status": "IDLE"})
    return {key: value for key, value in job.items() if key != "failed_ids"}


def launch():
    with document_lock(LOCK + "-start"):
        job = state.load(PATH)
        if job and job["status"] == "RUNNING":
            return status()
        job = {
            "id_job": str(uuid4()), "status": "RUNNING", "phase": "LIBRARY",
            "registered": 0, "withdrawn": 0, "failed_ids": [],
            "registration_failed": 0, "qualified": 0, "qualification_failed": 0,
            "updated_at": state.stamp(),
        }
        state.save(PATH, job)
        return status()


def run(id_job):
    from core.company.library_post_worker import _eligible, qualify_batch
    from core.company.library_post_bulk_import import register_batch

    while True:
        try:
            # Release between checkpoints. An interrupted pass can be resumed from
            # Library status and the verdict table, including across API processes.
            with document_lock(LOCK + "-batch"):
                job = state.load(PATH)
                if not job or job["id_job"] != id_job or job["status"] != "RUNNING":
                    return
                try:
                    if job["phase"] == "LIBRARY":
                        result = register_batch(
                            limit=IMPORT_BATCH_SIZE, excluded_ids=job["failed_ids"],
                        )
                        for key in ("registered", "withdrawn"):
                            job[key] += result[key]
                        job["failed_ids"].extend(result["failed_ids"])
                        job["registration_failed"] = len(job["failed_ids"])
                        if result["registered"] + result["withdrawn"] + result["failed"] < IMPORT_BATCH_SIZE:
                            job["phase"] = "QUALIFICATION"
                    else:
                        result = qualify_batch(historical=True, limit=BATCH_SIZE)
                        job["qualified"] += result["qualifies"]
                        job["qualification_failed"] += result["a_reprendre"]
                        if result["selectionnes"] == 0 or result["occupes"]:
                            remaining = bool(_eligible(historical=True, include_deferred=True, limit=1))
                            job["status"] = "PARTIAL" if remaining or job["registration_failed"] else "COMPLETE"
                except Exception:
                    logger.exception("Rattrapage Library interrompu")
                    job["status"] = "PARTIAL"
                    job["error"] = "Traitement interrompu. Consultez les logs backend, puis relancez le rattrapage."
                job["updated_at"] = state.stamp()
                state.save(PATH, job)
                if job["status"] != "RUNNING":
                    return
        except HTTPException as exc:
            if exc.status_code == 409:
                return
            raise
