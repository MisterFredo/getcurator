from typing import List

from core.numbers.backlog_service import get_numbers_backlog
from core.numbers.backlog_llm import process_backlog_row
from core.numbers.backlog_insert_service import insert_backlog_batch


def run_backlog_pipeline(limit: int = 100) -> dict:

    # ============================================================
    # 1. FETCH RAW BACKLOG
    # ============================================================

    rows = get_numbers_backlog(limit=limit)

    if not rows:
        return {
            "status": "ok",
            "processed": 0,
            "message": "No new backlog rows"
        }

    # ============================================================
    # 2. LLM PROCESSING
    # ============================================================

    results: List[dict] = []

    for r in rows:
        res = process_backlog_row(r)
        results.append(res)

    # ============================================================
    # 3. INSERT
    # ============================================================

    insert_backlog_batch(results)

    # ============================================================
    # 4. STATS
    # ============================================================

    keep = sum(1 for r in results if r.get("output", {}).get("decision") == "KEEP")
    reject = sum(1 for r in results if r.get("output", {}).get("decision") == "REJECT")

    return {
        "status": "ok",
        "processed": len(results),
        "keep": keep,
        "reject": reject,
    }
