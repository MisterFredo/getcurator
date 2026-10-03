from core.touch.edition_service import bootstrap_expert_touch_editions
from core.user.user_service import list_users


# ============================================================
# PREPARE MONTHLY EDITIONS FOR ACTIVE EXPERTS
# ============================================================

def bootstrap_all_expert_touch_editions(
    months_count: int = 3,
) -> dict:
    if months_count not in (1, 3):
        raise ValueError("Choisir le dernier mois ou les trois derniers mois.")

    experts = [
        expert
        for expert in (list_users(profile_type="EXPERT") or [])
        if expert.get("IS_ACTIVE") is not False
    ]

    result = {
        "status": "completed",
        "experts_count": len(experts),
        "processed_count": 0,
        "created_count": 0,
        "prepared_count": 0,
        "skipped_count": 0,
        "failed_count": 0,
        "experts": [],
    }

    for expert in experts:
        expert_id = expert.get("ID_USER")
        try:
            if not expert_id:
                raise ValueError("Identifiant expert manquant.")
            expert_result = bootstrap_expert_touch_editions(
                expert_id=expert_id,
                months_count=months_count,
            )
            for field in (
                "created_count", "prepared_count",
                "skipped_count", "failed_count",
            ):
                result[field] += expert_result.get(field, 0)
            result["experts"].append(expert_result)
        except Exception as exc:
            result["failed_count"] += 1
            result["experts"].append({
                "expert_id": expert_id,
                "status": "failed",
                "error": str(exc),
            })
        result["processed_count"] += 1

    if result["failed_count"]:
        result["status"] = (
            "partial"
            if result["prepared_count"] + result["skipped_count"]
            else "failed"
        )
    return result


def prepare_latest_all_expert_touch_editions() -> dict:
    return bootstrap_all_expert_touch_editions(months_count=1)
