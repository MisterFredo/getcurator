from datetime import datetime, timedelta, timezone

from core.touch.edition_repository import (
    build_touch_edition_id,
    claim_touch_edition,
    get_touch_edition,
    record_touch_edition_error,
    save_touch_edition_search,
)
from core.touch.expert_context_service import load_touch_expert_context
from core.touch.search_models import TouchResearchBrief
from core.touch.search_service import search_touch_contents
from core.user.user_service import get_user_by_id


BOOTSTRAP_TOUCH_MONTHS_COUNT = 3


# ============================================================
# COMPLETE MONTHS
# ============================================================

def build_touch_monthly_periods(
    count: int = BOOTSTRAP_TOUCH_MONTHS_COUNT,
    now: datetime | None = None,
) -> list[tuple[datetime, datetime]]:
    """Newest first; complete UTC months, inclusive end."""
    if count not in (1, 3):
        raise ValueError("Choisir le dernier mois ou les trois derniers mois.")

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    current = current.astimezone(timezone.utc)
    cursor = current.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    periods = []

    for _ in range(count):
        end = cursor - timedelta(microseconds=1)
        start = end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        periods.append((start, end))
        cursor = start

    return periods


# ============================================================
# PREPARE ONE EXPERT'S MONTHLY EDITIONS
# ============================================================

def bootstrap_expert_touch_editions(
    expert_id: str,
    months_count: int = BOOTSTRAP_TOUCH_MONTHS_COUNT,
    model: str | None = None,
) -> dict:
    """
    Prepare corpora only. Manual validation and notebook generation
    remain inside the existing Touch workflow.

    TO_REVIEW, GENERATED and BUILDING editions are not regenerated.
    ERROR editions are retried.
    """
    periods = build_touch_monthly_periods(months_count)
    expert_id = (expert_id or "").strip()
    account = get_user_by_id(expert_id) if expert_id else None

        if not account:
            raise ValueError("Profil Touch introuvable.")

    result = {
        "status": "completed",
        "expert_id": expert_id,
        "created_count": 0,
        "prepared_count": 0,
        "skipped_count": 0,
        "failed_count": 0,
        "editions": [],
    }

    if account.get("IS_ACTIVE") is False:
        result.update(status="not_eligible", reason="Expert inactif.")
        return result

    # Same eligibility as expert-backed Touch research:
    # a valid, READY structured profile with monitoring instructions.
    context = load_touch_expert_context(expert_id)
    language = account.get("LANGUAGE") or "fr"
    language = language if language in ("fr", "en") else "fr"

    for start, end in periods:
        edition_id = build_touch_edition_id(expert_id, start)
        item = {
            "edition_id": edition_id,
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
        }
        claimed = False

        try:
            existing = get_touch_edition(edition_id)
            if existing and existing["status"] != "ERROR":
                result["skipped_count"] += 1
                item.update(status=existing["status"], action="skipped")
                result["editions"].append(item)
                continue

            month = start.strftime("%Y-%m")
            subject = f"{context.display_name} — {month}"

            if language == "fr":
                query = (
                    f"Documenter les évolutions pertinentes pour le profil "
                    f"de {context.display_name} durant le mois {month}. "
                    "Respecter l'ensemble de ses instructions de suivi, "
                    "priorités professionnelles, critères de pertinence "
                    "et exclusions. Organiser la synthèse autour de ses "
                    "enjeux et des axes étayés par le corpus. "
                    "Distinguer faits nouveaux, analyses et pratiques "
                    "documentées. Ne pas inventer de faits, de liens avec "
                    "le profil ni de recommandations."
                )
            else:
                query = (
                    f"Document developments relevant to "
                    f"{context.display_name}'s profile during {month}. "
                    "Follow all monitoring instructions, professional "
                    "priorities, relevance criteria and exclusions. "
                    "Organize the synthesis around the profile's concerns "
                    "and axes supported by corpus evidence. Distinguish "
                    "new facts, analysis and documented practices. "
                    "Do not invent facts, connections to the profile "
                    "or recommendations."
                )

            claim_touch_edition(
                edition_id, expert_id, start, end, subject, language,
            )
            claimed = True
            if existing is None:
                result["created_count"] += 1

            outcome = search_touch_contents(
                brief=TouchResearchBrief(
                    query=query,
                    expert_id=expert_id,
                    output_language=language,
                    period_start=start,
                    period_end=end,
                ),
                model=model,
            )

            # An empty month still goes to manual review.
            # Search warnings are preserved for the administrator.
            save_touch_edition_search(
                edition_id=edition_id,
                search=outcome.model_dump(mode="json"),
            )
            result["prepared_count"] += 1
            item.update(
                status="TO_REVIEW",
                action="prepared",
                candidate_count=len(outcome.candidates),
                warnings=list(outcome.errors),
            )

        except Exception as exc:
            message = str(exc)
            if claimed:
                try:
                    record_touch_edition_error(edition_id, message)
                except Exception as persistence_exc:
                    message += f" | Enregistrement de l'erreur : {persistence_exc}"
            result["failed_count"] += 1
            item.update(status="ERROR", action="failed", error=message)

        result["editions"].append(item)

    if result["failed_count"]:
        result["status"] = (
            "partial"
            if result["prepared_count"] + result["skipped_count"]
            else "failed"
        )

    return result


def prepare_latest_expert_touch_edition(
    expert_id: str,
    model: str | None = None,
) -> dict:
    return bootstrap_expert_touch_editions(
        expert_id=expert_id,
        months_count=1,
        model=model,
    )
