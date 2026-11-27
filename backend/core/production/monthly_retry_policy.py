"""Bound technical rewrites and local repairs; one migration recovery only."""
from core.production.monthly_repair_rules import AUDIT_REVISION, REPAIR_KIND, repair_plan
from core.production.monthly_repair_revision import (
    REPAIR_REVISION, MAX_LEGACY_RECOVERY_REPAIRS,
)

MAX_DOCUMENT_ATTEMPTS = 4
MAX_LOCAL_REPAIRS = 2


def document_budget(history, read_artifact):
    documents = sorted(
        (row for row in history if row["stage"] == "DOCUMENT"),
        key=lambda row: row["version_number"], reverse=True,
    )
    loaded = {row["artifact_id"]: read_artifact(row) for row in documents}
    repairs = [
        row for row in documents
        if (loaded[row["artifact_id"]].get("request") or {}).get("kind") == REPAIR_KIND
    ]
    full_documents = [row for row in documents if row not in repairs]
    # Old in-flight operations keep their original contract. Their history is
    # retained; the current service may recover once, never reset its counters.
    legacy_repairs = [
        row for row in repairs
        if (loaded[row["artifact_id"]].get("request") or {}).get("repair_revision")
        != REPAIR_REVISION
    ]
    current_repairs = [row for row in repairs if row not in legacy_repairs]
    recovery = bool(
        len(repairs) >= MAX_LOCAL_REPAIRS
        and legacy_repairs
        and len(current_repairs) < MAX_LEGACY_RECOVERY_REPAIRS
        and len(repairs) < MAX_LOCAL_REPAIRS + MAX_LEGACY_RECOVERY_REPAIRS
    )
    repair_slot = len(repairs) < MAX_LOCAL_REPAIRS or recovery
    consecutive_failures = 0
    for row in documents:
        if row["status"] not in {"validation_failed", "incomplete"}:
            break
        consecutive_failures += 1
    document_ids = {row["artifact_id"] for row in documents}
    reviews = []
    for row in sorted(history, key=lambda r: r["version_number"], reverse=True):
        if row["stage"] not in {"REVIEW", "REVIEW_BATCH"} or row["status"] != "completed":
            continue
        item = read_artifact(row)
        if (item.get("request") or {}).get("document_artifact_id") not in document_ids:
            continue
        if ((item.get("result") or {}).get("review") or {}).get("passed") is False:
            reviews.append(item)
    latest = loaded[documents[0]["artifact_id"]] if documents else None
    assessment = next((
        review for review in reviews
        if latest
        and review["request"]["document_artifact_id"] == latest["artifact_id"]
        and review["request"].get("audit_revision") == AUDIT_REVISION
    ), None)
    local_repair = False
    unhandled_locations = []
    # Compute diagnostics even when no slot remains.
    if latest and latest["status"] == "completed" and assessment:
        plan = repair_plan(
            (latest.get("result") or {}).get("document") or {},
            assessment["result"]["review"]["issues"],
        )
        unhandled_locations = plan["unhandled_locations"]
        local_repair = bool(repair_slot and plan["targets"] and not unhandled_locations)
    # Technical rewrites remain forbidden after a localized repair.
    regular_correction = bool(
        len(full_documents) < MAX_DOCUMENT_ATTEMPTS
        and consecutive_failures < 2
        and latest is not None
        and latest["status"] in {"validation_failed", "incomplete"}
        and (latest.get("request") or {}).get("kind") != REPAIR_KIND
    )
    max_repairs = MAX_LOCAL_REPAIRS + (
        MAX_LEGACY_RECOVERY_REPAIRS if legacy_repairs else 0
    )
    return {
        "document_attempts": len(documents),
        "technical_failures": sum(
            row["status"] in {"validation_failed", "incomplete"} for row in documents
        ),
        "failed_reviews": len(reviews),
        "full_document_attempts": len(full_documents),
        "local_repair_attempts": len(repairs),
        "max_document_attempts": MAX_DOCUMENT_ATTEMPTS + max_repairs,
        "max_full_document_attempts": MAX_DOCUMENT_ATTEMPTS,
        "max_editorial_corrections": max_repairs,
        "targeted_repair_available": local_repair,
        "unhandled_locations": unhandled_locations,
        "can_correct": regular_correction or local_repair,
    }
