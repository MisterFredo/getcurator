"""Bound full technical rewrites and localized editorial repairs separately."""
from core.production.monthly_repair_rules import AUDIT_REVISION, REPAIR_KIND, repair_targets

MAX_DOCUMENT_ATTEMPTS = 4
MAX_LOCAL_REPAIRS = 2


def document_budget(history, read_artifact):
    documents = sorted((row for row in history if row["stage"] == "DOCUMENT"),
                       key=lambda row: row["version_number"], reverse=True)
    loaded = {row["artifact_id"]: read_artifact(row) for row in documents}
    repairs = [row for row in documents if (loaded[row["artifact_id"]].get("request") or {}).get("kind") == REPAIR_KIND]
    full_documents = [row for row in documents if row not in repairs]
    consecutive_failures = 0
    for row in documents:
        if row["status"] not in {"validation_failed", "incomplete"}:
            break
        consecutive_failures += 1
    reviews = []
    document_ids = {row["artifact_id"] for row in documents}
    for row in history:
        if row["stage"] not in {"REVIEW", "REVIEW_BATCH"} or row["status"] != "completed":
            continue
        item = read_artifact(row)
        if (item.get("request") or {}).get("document_artifact_id") not in document_ids:
            continue
        review = (item.get("result") or {}).get("review") or {}
        if review.get("passed") is False:
            reviews.append(item)
    local_repair = False
    if len(repairs) < MAX_LOCAL_REPAIRS:
        latest = loaded[documents[0]["artifact_id"]] if documents else None
        assessment = next((review for review in reviews
                           if latest and review["request"]["document_artifact_id"] == latest["artifact_id"]
                           and review["request"].get("audit_revision") == AUDIT_REVISION), None)
        if latest and latest["status"] == "completed" and assessment:
            local_repair = bool(repair_targets(
                (latest.get("result") or {}).get("document") or {}, assessment["result"]["review"]["issues"],
            ))
    # Full rewrites recover technical failures only. Editorial findings use
    # bounded field repairs after the exhaustive, page-scoped assessment.
    latest = loaded[documents[0]["artifact_id"]] if documents else None
    regular_correction = (len(full_documents) < MAX_DOCUMENT_ATTEMPTS and consecutive_failures < 2
                          and latest is not None and latest["status"] in {"validation_failed", "incomplete"}
                          and (latest.get("request") or {}).get("kind") != REPAIR_KIND)
    return {
        "document_attempts": len(documents),
        "technical_failures": sum(row["status"] in {"validation_failed", "incomplete"} for row in documents),
        "failed_reviews": len(reviews),
        "full_document_attempts": len(full_documents), "local_repair_attempts": len(repairs),
        "max_document_attempts": MAX_DOCUMENT_ATTEMPTS + MAX_LOCAL_REPAIRS,
        "max_full_document_attempts": MAX_DOCUMENT_ATTEMPTS,
        "max_editorial_corrections": MAX_LOCAL_REPAIRS,
        "targeted_repair_available": local_repair,
        "can_correct": regular_correction or local_repair,
    }
