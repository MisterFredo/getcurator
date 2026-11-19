"""Single-process background job for RAW destocking.

Requires exactly one backend process/instance. Does not survive process restart.
"""
import logging
import threading
import uuid
from datetime import datetime, timezone
from typing import Callable, Any

logger = logging.getLogger(__name__)
_lock = threading.Lock()
_state_lock = threading.Lock()
_state = {
    "status": "IDLE", "job_id": None, "started_at": None,
    "finished_at": None, "processed": None, "errors": None,
    "result": None, "error": None,
}


def _now():
    return datetime.now(timezone.utc).isoformat()


def get_destock_status() -> dict:
    with _state_lock:
        return dict(_state)


def update_destock_progress(processed: int, errors: int) -> None:
    with _state_lock:
        _state['processed'] = processed
        _state['errors'] = errors


def start_destock_job(work: Callable[[], Any]) -> dict | None:
    """Returns None if already running, otherwise starts a daemon thread."""
    if not _lock.acquire(blocking=False):
        return None

    job_id = str(uuid.uuid4())
    with _state_lock:
        _state.update(status="RUNNING", job_id=job_id, started_at=_now(),
                      finished_at=None, processed=None, errors=None,
                      result=None, error=None)

    def run():
        try:
            result = work()
            with _state_lock:
                _state.update(status="COMPLETED", finished_at=_now(), result=result)
                if isinstance(result, dict):
                    for key in ("processed", "errors", "total_processed", "total_errors"):
                        if isinstance(result.get(key), int):
                            target = {'total_processed': 'processed', 'total_errors': 'errors'}.get(key, key)
                            _state[target] = result[key]
        except Exception as exc:
            logger.exception("RAW destock job failed: %s", job_id)
            with _state_lock:
                _state.update(status="ERROR", finished_at=_now(), error=str(exc))
        finally:
            _lock.release()

    try:
        threading.Thread(target=run, name=f"raw-destock-{job_id[:8]}", daemon=True).start()
    except Exception:
        with _state_lock:
            _state.update(status="ERROR", finished_at=_now(), error="Unable to start thread")
        _lock.release()
        raise
    return get_destock_status()
