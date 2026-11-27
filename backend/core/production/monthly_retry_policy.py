"""Separate technical recovery from the single editorial correction round."""
from core.production.monthly_repair_rules import REPAIR_KIND, repair_targets

MAX_DOCUMENT_ATTEMPTS = 4
MAX_FAILED_REVIEWS = 2


def document_budget(history, read_artifact):
    documents = sorted((row for row in history if row["stage"] == "DOCUMENT"),
                       key=lambda row: row["version_number"], reverse=True)
    consecutive_failures = 0
    for row in documents:
        if row["status"] not in {"validation_failed", "incomplete"}:
            break
        consecutive_failures += 1
    reviews = []
    document_ids = {row["artifact_id"] for row in documents}
    for row in history:
        if row["stage"] != "REVIEW" or row["status"] != "completed":
            continue
        item = read_artifact(row)
        if (item.get("request") or {}).get("document_artifact_id") not in document_ids:
            continue
        review = (item.get("result") or {}).get("review") or {}
        if review.get("passed") is False:
            reviews.append(item)
    local_repair = False
    if len(documents) < MAX_DOCUMENT_ATTEMPTS and len(reviews) == MAX_FAILED_REVIEWS:
        latest = read_artifact(documents[0]) if documents else None
        assessment = next((review for review in reviews
                           if latest and review["request"]["document_artifact_id"] == latest["artifact_id"]), None)
        if latest and latest["status"] == "completed" and assessment:
            used = any((read_artifact(row).get("request") or {}).get("kind") == REPAIR_KIND for row in documents)
            local_repair = not used and bool(repair_targets(
                (latest.get("result") or {}).get("document") or {}, assessment["result"]["review"]["issues"],
            ))
    regular_correction = (len(documents) < MAX_DOCUMENT_ATTEMPTS
                          and len(reviews) < MAX_FAILED_REVIEWS and consecutive_failures < 2)
    return {
        "document_attempts": len(documents),
        "technical_failures": sum(row["status"] in {"validation_failed", "incomplete"} for row in documents),
        "failed_reviews": len(reviews),
        "max_document_attempts": MAX_DOCUMENT_ATTEMPTS,
        "max_editorial_corrections": MAX_FAILED_REVIEWS - 1,
        "targeted_repair_available": local_repair,
        "can_correct": regular_correction or local_repair,
    }
