"""Save the company report for a specific corpus and Notebook revision."""

import json
from datetime import datetime, timezone

from fastapi import HTTPException
from google.api_core.exceptions import PreconditionFailed

from core.company import company_report_corpus as corpus
from core.company import company_report_notebook as notebooks
from core.company import watch_discovery_service as discovery
from core.library import company_watch_library as library
from utils.gcs import bucket


def _report_path(company_id, month, revision):
    _, _, _, path = notebooks._saved_corpus(company_id, month, revision)
    return path.removesuffix(".json") + "/report.json", path


def get_report(company_id, month, revision):
    path, _ = _report_path(company_id, month, revision)
    report, _ = corpus._read_draft(path)
    return {"report": report}


def build_report(notebook, company_name):
    sources = {source["id"]: source for source in notebook["sources"]}
    coverage = {}
    for source in sources.values():
        kind = source["source_kind"]
        coverage[kind] = coverage.get(kind, 0) + 1

    sections = {"facts": [], "site_changes": [], "mentions": []}
    for fact in notebook["facts"]:
        primary = sources[fact["primary_id"]]
        kind = primary["source_kind"]
        section = {"SITE_CHANGE": "site_changes", "MENTION": "mentions"}.get(kind, "facts")
        sections[section].append({
            **fact,
            "reference_date": primary["source_at"],
            "date_kind": primary["date_kind"],
        })

    return {
        "schema_version": 1,
        "company_id": notebook["company_id"],
        "company_name": company_name,
        "month": notebook["month"],
        "revision": notebook["revision"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "coverage": coverage,
        "limited_sources": sum(source["text_status"] != "FULL" for source in sources.values()),
        "sections": sections,
        "sources": list(sources.values()),
    }


def generate_report(company_id, month, revision):
    path, notebook_path = _report_path(company_id, month, revision)
    existing, _ = corpus._read_draft(path)
    if existing is not None:
        return {"report": existing}
    notebook, _ = corpus._read_draft(notebook_path)
    if notebook is None:
        raise HTTPException(409, "Générez le Notebook de cette révision avant de créer le rapport.")
    rows = library._query(
        f"SELECT NAME FROM `{discovery.COMPANY}` WHERE ID_COMPANY=@company LIMIT 1",
        [library._p("company", "STRING", company_id)],
    )
    report = build_report(notebook, rows[0]["NAME"] if rows else company_id)
    _report_path(company_id, month, revision)
    try:
        bucket.blob(path).upload_from_string(
            json.dumps(report, ensure_ascii=False), content_type="application/json", if_generation_match=0,
        )
    except PreconditionFailed:
        report, _ = corpus._read_draft(path)
        if report is None:
            raise
    return {"report": report}
