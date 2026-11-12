"""Manual monthly report batch, shared by Veille and Cockpit."""
import json
import logging
import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import HTTPException

from core.company import company_report as reports
from core.company import company_report_corpus as corpus
from core.company import company_report_notebook as notebooks
from core.company.watch_operations_query import list_active_companies
from core.library import company_watch_library as library
from utils.gcs import bucket

logger = logging.getLogger(__name__)
ROOT = f"company-reports/batches/{library.BASE}"
STATE = ROOT + "/latest.json"
LOCK = "monthly-report-batch-" + library.BASE


def options():
    today = datetime.now(ZoneInfo("Europe/Paris")).date()
    month = (today.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    return {"month": month, **list_active_companies()}


def status():
    return {"job": corpus._read_draft(STATE)[0]}


def save(job, revision):
    job["updated_at"] = datetime.now(timezone.utc).isoformat()
    blob = bucket.blob(STATE)
    blob.upload_from_string(json.dumps(job, ensure_ascii=False),
                            content_type="application/json", if_generation_match=int(revision))
    return str(blob.generation)


def start(month, company_ids, language):
    with library.document_lock(LOCK):
        job, revision = corpus._read_draft(STATE)
        if job and job["status"] == "RUNNING":
            raise HTTPException(409, "Un lot est déjà en cours. Actualisez son suivi.")
        available = options()
        if month != available["month"]:
            raise HTTPException(409, "Le dernier mois clôturé a changé. Actualisez la sélection.")
        selected = set(company_ids)
        eligible = {row["id_company"]: row["name"] for row in available["companies"]}
        if not selected or not selected <= eligible.keys():
            raise HTTPException(400, "Sélectionnez des sociétés suivies et actives.")
        job = {
            "month": month, "language": language, "status": "RUNNING",
            "companies": [{"id_company": key, "name": name, "status": "PENDING"}
                          for key, name in eligible.items() if key in selected],
        }
        return save(job, revision)


def process(company, month, language):
    draft = corpus.get_corpus(company, month)
    revision = draft["revision"]
    if draft["unavailable_count"]:
        return "REVIEW", "Des sources du corpus enregistré sont indisponibles."
    if not draft["selected_ids"]:
        return "EMPTY", "Aucune source sélectionnée pour ce mois."
    if revision != "0" and reports.get_report(company, month, revision, language)["report"]:
        return "EXISTING", None
    if len(draft["selected_ids"]) > notebooks.MAX_SOURCES:
        return "REVIEW", f"Le corpus dépasse {notebooks.MAX_SOURCES} sources. Ouvrez-le pour ajuster la sélection."
    if revision == "0":
        revision = corpus.save_corpus(company, month, draft["selected_ids"], revision)["revision"]
    if notebooks.get_notebook(company, month, revision)["notebook"] is None:
        notebooks.generate_notebook(company, month, revision)
    reports.generate_report(company, month, revision, language)
    return "READY", None


def drain(expected_revision):
    while True:
        try:
            with library.document_lock(LOCK):
                job, revision = corpus._read_draft(STATE)
                if revision != expected_revision or job["status"] != "RUNNING":
                    return
                item = next(row for row in job["companies"] if row["status"] == "PENDING")
                try:
                    item["status"], item["message"] = process(item["id_company"], job["month"], job["language"])
                except Exception:
                    logger.exception("Monthly report failed company=%s month=%s", item["id_company"], job["month"])
                    item.update(status="FAILED", message="Échec de génération. Réessayez ou ouvrez le rapport.")
                if not any(row["status"] == "PENDING" for row in job["companies"]):
                    job["status"] = "COMPLETE"
                expected_revision = save(job, revision)
                if job["status"] == "COMPLETE":
                    return
        except HTTPException as exc:
            if exc.status_code != 409:
                raise
            return


def resume():
    with library.document_lock(LOCK):
        job, revision = corpus._read_draft(STATE)
        if job is None:
            raise HTTPException(404, "Aucun lot à reprendre.")
        if job["status"] == "RUNNING":
            return revision
        failed = [row for row in job["companies"] if row["status"] == "FAILED"]
        if not failed:
            raise HTTPException(409, "Aucune génération en échec à reprendre.")
        for row in failed:
            row.update(status="PENDING", message=None)
        job["status"] = "RUNNING"
        return save(job, revision)


def history():
    from core.company import watch_service as watch

    rows = library._query(f"SELECT ID_COMPANY, NAME FROM `{watch.COMPANY}`")
    companies = {corpus._scope(row["ID_COMPANY"], "2000-01")[2].split("/")[-2]: row for row in rows}
    prefix = "company-reports/corpus/"
    paths = {blob.name: blob.generation for blob in bucket.list_blobs(prefix=prefix)}
    entries = []
    for path, revision in paths.items():
        match = re.fullmatch(prefix + r"([a-f0-9]{64})/([0-9]{4}-[0-9]{2})\.json", path)
        if not match or match[1] not in companies:
            continue
        row = companies[match[1]]
        notebook = notebooks._path(path, str(revision))
        languages = [lang for lang in ("fr", "en") if
                     notebook.removesuffix(".json") + f"/report-{lang}-signature-v2.json" in paths]
        entries.append({"id_company": row["ID_COMPANY"], "name": row["NAME"], "month": match[2],
                        "revision": str(revision), "languages": languages, "has_notebook": notebook in paths})
    entries.sort(key=lambda row: row["name"].casefold())
    entries.sort(key=lambda row: row["month"], reverse=True)
    return {"reports": entries}
