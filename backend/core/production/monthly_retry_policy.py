"""Separate technical recovery from the single editorial correction round."""

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
    return {
        "document_attempts": len(documents),
        "technical_failures": sum(row["status"] in {"validation_failed", "incomplete"} for row in documents),
        "failed_reviews": len(reviews),
        "max_document_attempts": MAX_DOCUMENT_ATTEMPTS,
        "max_editorial_corrections": MAX_FAILED_REVIEWS - 1,
        "can_correct": (len(documents) < MAX_DOCUMENT_ATTEMPTS
                        and len(reviews) < MAX_FAILED_REVIEWS and consecutive_failures < 2),
    }
