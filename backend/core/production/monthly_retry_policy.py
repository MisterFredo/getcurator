"""Fixed per-page correction budgets, including all saved legacy attempts."""
from core.production.monthly_repair_rules import AUDIT_REVISION, REPAIR_KIND
from core.production.monthly_repair_contract import MAX_PAGE_REPAIRS, EDITORIAL_EDIT_KIND, PROPOSAL_STAGE, CHECK_STAGE, VERIFIED_DOCUMENT_KIND, repair_plan, page_budget

MAX_DOCUMENT_ATTEMPTS = 4


def document_budget(history, read_artifact):
    details = {}
    def read(row):
        if row["artifact_id"] not in details:
            details[row["artifact_id"]] = read_artifact(row) or {}
        return details[row["artifact_id"]]
    documents = sorted((r for r in history if r["stage"] == "DOCUMENT"),
                       key=lambda r: r["version_number"], reverse=True)
    legacy_repairs = [r for r in documents if (read(r).get("request") or {}).get("kind") == REPAIR_KIND]
    proposals = [r for r in history if r["stage"] == PROPOSAL_STAGE and (read(r).get("request") or {}).get("mode") == "AUTOMATIC"]
    repairs = legacy_repairs + proposals
    verified = [r for r in documents if (read(r).get("request") or {}).get("kind") == VERIFIED_DOCUMENT_KIND]
    editorial = [r for r in documents if (read(r).get("request") or {}).get("kind") == EDITORIAL_EDIT_KIND]
    full = [r for r in documents if r not in repairs and r not in editorial and r not in verified]
    latest = read(documents[0]) if documents else None
    reviews = []
    for row in sorted(history, key=lambda r: r["version_number"], reverse=True):
        if row["stage"] not in {"REVIEW", "REVIEW_BATCH"} or row["status"] != "completed":
            continue
        item = read(row)
        if ((item.get("result") or {}).get("review") or {}).get("passed") is False:
            reviews.append(item)
    assessment = next((r for r in reviews if latest
        and (r.get("request") or {}).get("document_artifact_id") == latest["artifact_id"]
        and r["request"].get("audit_revision") == AUDIT_REVISION), None)
    available, unhandled, exhausted, errors = False, [], [], []
    counts = {}
    if latest and latest["status"] == "completed":
        document = (latest.get("result") or {}).get("document") or {}
        budget = page_budget(history, read, document, REPAIR_KIND)
        counts, errors = budget["attempts_by_page"], budget["errors"]
        if assessment:
            plan = repair_plan(document, assessment["result"]["review"]["issues"])
            unhandled = plan["unhandled_locations"]
            exhausted = [p for p in plan["page_ids"] if counts.get(p, 0) >= MAX_PAGE_REPAIRS]
            available = bool(plan["targets"] and not (unhandled or exhausted or errors))
    consecutive = 0
    for row in documents:
        if row["status"] not in {"validation_failed", "incomplete"}:
            break
        consecutive += 1
    # A localized validation/submission failure never authorizes a full rewrite.
    regular = bool(latest and latest["status"] in {"validation_failed", "incomplete"}
                   and (latest.get("request") or {}).get("kind") not in {REPAIR_KIND, EDITORIAL_EDIT_KIND, VERIFIED_DOCUMENT_KIND}
                   and len(full) < MAX_DOCUMENT_ATTEMPTS and consecutive < 2)
    last_phase = next((read(r) for r in sorted(history, key=lambda r: r["version_number"], reverse=True)
                       if r["stage"] in {PROPOSAL_STAGE, CHECK_STAGE} and latest
                       and (read(r).get("request") or {}).get("document_artifact_id") == latest["artifact_id"]
                       and (read(r).get("request") or {}).get("mode") == "AUTOMATIC"), None)
    if last_phase and last_phase["status"] not in {"completed", "STARTING", "queued", "in_progress", "SUBMISSION_UNKNOWN"}:
        available = False
    # Compatibility for the existing UI: this is an upper bound on operations,
    # not a counter that gets reset after a failed review. Multi-page operations
    # consume one slot on each affected page.
    max_local = max(len(repairs), sum(max(MAX_PAGE_REPAIRS, n) for n in counts.values()))
    return {"document_attempts": len(documents),
            "technical_failures": sum(r["status"] in {"validation_failed", "incomplete", "failed"} for r in history if r["stage"] in {"DOCUMENT", PROPOSAL_STAGE, CHECK_STAGE}),
            "failed_reviews": len(reviews), "full_document_attempts": len(full),
            "local_repair_attempts": len(repairs), "editorial_edit_count": len(editorial), "verified_correction_count": len(verified),
            "automatic_proposal_count": len(proposals),
            "max_document_attempts": MAX_DOCUMENT_ATTEMPTS + max_local,
            "max_full_document_attempts": MAX_DOCUMENT_ATTEMPTS,
            "max_editorial_corrections": max_local,
            "correction_budget_unit": "PAGE", "max_corrections_per_page": MAX_PAGE_REPAIRS,
            "page_correction_attempts": counts, "exhausted_page_ids": exhausted,
            "correction_history_errors": errors,
            "targeted_repair_available": available, "unhandled_locations": unhandled,
            "can_correct": regular or available}
