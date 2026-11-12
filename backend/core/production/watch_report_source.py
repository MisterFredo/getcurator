"""Read the exact saved watch report selected for a production."""

from datetime import date
from uuid import NAMESPACE_URL, uuid5

from fastapi import HTTPException

from core.company.company_report import get_report
from core.production.models import ProductionWatchReportRef


def read_watch_report(ref: ProductionWatchReportRef) -> tuple[str, int, dict]:
    try:
        result = get_report(ref.company_id, ref.month, ref.revision, ref.language)
    except HTTPException as exc:
        if exc.status_code == 409:
            raise ValueError("Le rapport de veille a changé. Actualisez la sélection.") from exc
        raise

    report = result.get("report")
    if not report:
        raise ValueError(f"Rapport de veille indisponible : {ref.company_id} · {ref.month} · {ref.language}.")
    expected = ref.model_dump()
    if any(report.get(field) != value for field, value in expected.items()):
        raise ValueError("La version du rapport de veille ne correspond pas à la sélection.")

    key = f"getcurator/watch-report/{ref.company_id}/{ref.month}/{ref.language}/{ref.revision}"
    report_id = str(uuid5(NAMESPACE_URL, key))
    start = date.fromisoformat(ref.month + "-01")
    end = date(start.year + (start.month == 12), start.month % 12 + 1, 1)
    payload = {
        **report,
        "source_type": "COMPANY_WATCH",
        "report_id": report_id,
        "version_number": 1,
        "subject": f"{report['company_name']} · {ref.month} · {ref.language.upper()}",
        "output_language": ref.language,
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
    }
    return report_id, 1, payload
