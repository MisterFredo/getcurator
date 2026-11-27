"""Bounded report workers; API/background-request threads never wait in line."""
import logging
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)
MAX_REPORTS = 4
_POOL = ThreadPoolExecutor(max_workers=MAX_REPORTS, thread_name_prefix="monthly-report")
_GUARD = threading.Lock()
_PENDING = set()
_RUNNING = set()
_RECOVERIES = {}


def enqueue(production_id, response_id=None):
    with _GUARD:
        if response_id:
            recoveries = _RECOVERIES.setdefault(production_id, [])
            if response_id not in recoveries:
                recoveries.append(response_id)
        if production_id in _PENDING:
            return
        _PENDING.add(production_id)
        _POOL.submit(_work, production_id)


def _work(production_id):
    from core.production.monthly_service import _run_background
    with _GUARD:
        _RUNNING.add(production_id)
    while True:
        with _GUARD:
            values = _RECOVERIES.get(production_id) or []
            response_id = values.pop(0) if values else None
        try:
            _run_background(production_id, response_id)
        except Exception:
            logger.exception("Monthly worker interrupted; durable workflow can resume: %s", production_id)
        with _GUARD:
            if _RECOVERIES.get(production_id):
                continue
            _PENDING.discard(production_id)
            _RUNNING.discard(production_id)
            _RECOVERIES.pop(production_id, None)
            return


def position(production_id):
    with _GUARD:
        return {"queued": production_id in _PENDING and production_id not in _RUNNING,
                "running": production_id in _RUNNING, "max_reports": MAX_REPORTS}
