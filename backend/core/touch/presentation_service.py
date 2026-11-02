"""One saved Touch report -> editorial presentation, with frozen evidence."""
import hashlib
import json
import logging
import os
from types import SimpleNamespace
from pydantic import BaseModel, ConfigDict, Field
from openai import APIStatusError
from core.production.document_models import ProductionDocument
from core.production.document_service import client, validate_against_corpus, numbers_in_quote
from core.touch.notebook_report_service import get_touch_report
from core.touch import presentation_repository as repo
from core.touch.presentation_prompt import INSTRUCTIONS

logger = logging.getLogger(__name__)
WORKFLOW = "getcurator_touch_presentation_v1"


class Coverage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    section_id: str
    page_ids: list[str]
    omitted_details: str


class PresentationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    document: ProductionDocument
    section_coverage: list[Coverage]


def freeze_report(report):
    keys = ("report_id", "version_number", "subject", "objective", "output_language",
            "period_start", "period_end", "content_ids", "sources", "notebook")
    payload = {key: report.get(key) for key in keys}
    # Standalone canonical numbers are not the presentation's content source.
    payload["notebook"] = {key: value for key, value in report["notebook"].items()
                           if key not in {"validated_numbers", "quarantined_numbers"}}
    return json.loads(json.dumps(payload, ensure_ascii=False, allow_nan=False, default=str))


def snapshot_hash(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False,
                                    allow_nan=False, separators=(",", ":")).encode()).hexdigest()


def build_evidence(report):
    evidence = []
    saved = {s["content_id"]: s for s in report.get("sources", [])}
    fields = {"notes": ("statement", "explanation"), "events": ("title", "description"),
              "executive_summary": ("statement",), "cross_readings": ("title", "statement"),
              "timeline": ("label", "description"), "contradictions": ("subject", "description", "resolution")}
    for collection, names in fields.items():
        for i, item in enumerate(report["notebook"].get(collection, [])):
            content_id = next((cid for cid in item.get("source_content_ids", []) if cid in saved), None)
            label = str((saved.get(content_id) or {}).get("title") or report["subject"])[:300]
            for name in names:
                text = item.get(name)
                if not isinstance(text, str) or not text.strip():
                    continue
                # Exact scalar substrings, bounded by DocumentSource's quote contract.
                start = 0
                while start < len(text):
                    stop = min(start + 1100, len(text))
                    if stop < len(text):
                        boundary = text.rfind(" ", start + 500, stop)
                        if boundary > start:
                            stop = boundary
                    quote = text[start:stop]
                    if quote.strip():
                        evidence.append({"id": f"S{len(evidence)+1:04d}", "report_id": report["report_id"],
                            "report_version": report["version_number"],
                            "json_pointer": f"/notebook/{collection}/{i}/{name}", "quote": quote,
                            "content_id": content_id, "label": label})
                    start = stop
    return evidence


def _restore_omitted_sources(payload, snapshot):
    """Restore only missing entries already present in the frozen evidence registry.

    This runs before ProductionDocument's structural validator. Existing source
    objects, page references and prose are never rewritten or removed. Unknown
    references still fail; all provenance/numeric/coverage checks run afterwards.
    """
    if not isinstance(payload, dict) or not isinstance(payload.get("document"), dict):
        return []
    document = payload["document"]
    sources = document.get("sources")
    pages = document.get("pages")
    if not isinstance(sources, list) or not isinstance(pages, list):
        return []  # The normal schema validator will explain the invalid shape.
    evidence = {item["id"]: item for item in snapshot["evidence"]}
    present = {source.get("id") for source in sources
               if isinstance(source, dict) and isinstance(source.get("id"), str)}
    missing = []
    for page in pages:
        if not isinstance(page, dict) or not isinstance(page.get("source_ids"), list):
            continue
        for source_id in page["source_ids"]:
            if not isinstance(source_id, str) or source_id in present:
                continue
            if source_id not in evidence:
                raise ValueError(
                    f"Page {page.get('page_id', '?')} : source {source_id} "
                    "absente du registre de preuves figé. Aucune réparation automatique possible."
                )
            # Copy the exact registered entry, never reconstruct or paraphrase it.
            sources.append(dict(evidence[source_id]))
            present.add(source_id)
            missing.append(source_id)
    if missing:
        logger.warning("Touch presentation: restored omitted frozen sources %s", missing)
    return missing


def validate_result(text, snapshot):
    payload = json.loads(text)
    restored = _restore_omitted_sources(payload, snapshot)
    result = PresentationResult.model_validate(payload)
    report = snapshot["saved_report"]
    evidence = {item["id"]: item for item in snapshot["evidence"]}
    for source in result.document.sources:
        if source.model_dump(mode="json") != evidence.get(source.id):
            raise ValueError(f"Source {source.id} : preuve modifiée ou inconnue.")
    corpus = SimpleNamespace(reports=[SimpleNamespace(report_id=report["report_id"],
                            version_number=report["version_number"], payload=report)])
    validate_against_corpus(result.document, corpus)
    sources = {s.id: s for s in result.document.sources}
    pages = {p.page_id: p for p in result.document.pages}
    if not any(p.layout == "SUMMARY" for p in result.document.pages):
        raise ValueError("Une synthèse des enseignements est obligatoire.")
    for page in result.document.pages:
        if page.layout == "METRICS" or page.metrics:
            raise ValueError("Les chiffres doivent rester contextualisés dans les explications.")
        if page.layout not in {"COVER", "SOURCES"}:
            # Presence check only, not a semantic assertion. Reuse Production's
            # conservative parser for every number written in the narrative.
            allowed = set()
            for sid in page.source_ids:
                allowed |= numbers_in_quote(sources[sid].quote)
            written = numbers_in_quote(" ".join([page.title, *page.paragraphs, *page.bullets,
                                                page.takeaway, *page.cautions]))
            if written - allowed:
                raise ValueError(f"Page {page.page_id} : valeurs sans preuve citée : "
                                 + ", ".join(sorted(str(v) for v in written - allowed)))
    sections = report["notebook"].get("sections", [])
    expected = {s["section_id"] for s in sections}
    actual = [c.section_id for c in result.section_coverage]
    if set(actual) != expected or len(actual) != len(set(actual)):
        raise ValueError("La couverture doit référencer chaque chapitre exactement une fois.")
    notes = report["notebook"].get("notes", [])
    events = report["notebook"].get("events", [])
    for section in sections:
        coverage = next(c for c in result.section_coverage if c.section_id == section["section_id"])
        note_ids = set(section.get("note_ids", []))
        for event in events:
            if event["event_id"] in section.get("event_ids", []):
                note_ids.update(event.get("note_ids", []))
        pointers = {f"/notebook/notes/{i}/" for i, note in enumerate(notes) if note["note_id"] in note_ids}
        pointers |= {f"/notebook/events/{i}/" for i, event in enumerate(events)
                     if event["event_id"] in section.get("event_ids", [])}
        if pointers and not coverage.page_ids:
            raise ValueError(f"Chapitre omis : {section['title']}.")
        for pid in coverage.page_ids:
            page = pages.get(pid)
            if not page or page.layout in {"COVER", "SOURCES"}:
                raise ValueError("Couverture : page inconnue ou sans contenu éditorial.")
            if pointers and not any(sources[sid].json_pointer.startswith(tuple(pointers))
                                    for sid in page.source_ids):
                raise ValueError(f"Chapitre {section['title']} : page sans preuve du chapitre.")
    validated = result.model_dump(mode="json")
    validated["restored_source_ids"] = restored
    return validated


def public(item):
    if not item:
        return None
    return {key: value for key, value in item.items() if key != "request"}


def _required_report(report_id):
    report = get_touch_report(report_id)
    if not report:
        raise LookupError("Rapport Touch introuvable.")
    return report


def _serialize(response, item):
    metadata = response.metadata or {}
    if (metadata.get("workflow") != WORKFLOW or metadata.get("report_id") != item["report_id"]
        or metadata.get("artifact_id") != item["artifact_id"]
        or metadata.get("snapshot_sha256") != item["snapshot_sha256"]):
        raise ValueError("La réponse ne correspond pas à cette présentation et à son rapport figé.")
    job = {"id": response.id, "status": response.status, "model": response.model,
           "text": response.output_text or "", "document": None, "section_coverage": [],
           "export_context": {k: item["request"]["saved_report"].get(k) for k in ("subject", "output_language", "period_start", "period_end")},
           "error": response.error.model_dump(mode="json") if response.error else None,
           "usage": response.usage.model_dump(mode="json") if response.usage else None,
           "incomplete_details": response.incomplete_details.model_dump(mode="json") if response.incomplete_details else None,
           "validation_notes": ["Schéma, citations, provenance, couverture des chapitres et présence numérique contrôlés.",
             "Ces contrôles ne prouvent pas les causalités, unités ou interprétations : relecture éditoriale nécessaire."]}
    if response.status == "completed":
        try:
            job.update(validate_result(job["text"], item["request"]))
        except (ValueError, KeyError, IndexError) as exc:
            job["status"] = "validation_failed"
            job["error"] = {"message": str(exc)}
    return job


def start_presentation(report_id, artifact_id, expected_version):
    # Resolve local configuration before reserving a durable generation lock.
    model = os.getenv("TOUCH_PRESENTATION_MODEL") or os.getenv("PRODUCTION_DOCUMENT_MODEL") or os.getenv("PRODUCTION_PDF_MODEL") or "gpt-5.4"
    existing = repo.get_artifact(report_id, artifact_id)
    if existing:
        if existing["report_version"] != expected_version:
            raise ValueError("Cette clé correspond à une autre version de rapport.")
        return public(existing)
    report = _required_report(report_id)
    if report["version_number"] != expected_version:
        raise repo.PresentationConflict("Le rapport a changé. Rechargez-le avant de générer la présentation.")
    saved = freeze_report(report)
    evidence = build_evidence(saved)
    if not evidence:
        raise ValueError("Le rapport ne contient aucune preuve exploitable.")
    frozen_hash = snapshot_hash(saved)
    snapshot = {"saved_report": saved, "evidence": evidence, "prompt_version": WORKFLOW}
    with client() as connection:
        item, created = repo.reserve(report_id, artifact_id, expected_version, frozen_hash, snapshot)
        if not created:
            return public(item)
        try:
            response = connection.responses.create(model=model, instructions=INSTRUCTIONS,
                input=json.dumps({"output_language": saved["output_language"], **snapshot}, ensure_ascii=False, allow_nan=False),
                text={"format": {"type": "json_schema", "name": "touch_presentation", "strict": True,
                                 "schema": PresentationResult.model_json_schema()}},
                reasoning={"effort": "medium"}, max_output_tokens=32000, background=True, store=True,
                metadata={"workflow": WORKFLOW, "report_id": report_id, "artifact_id": item["artifact_id"],
                          "snapshot_sha256": frozen_hash})
            # Durable ID before parsing/validation; never retry inference automatically.
            logger.info("Touch presentation accepted: report=%s artifact=%s response=%s", report_id, artifact_id, response.id)
            repo.save_job(report_id, artifact_id, {"id": response.id, "status": "queued", "model": response.model})
            job = _serialize(response, item)
        except Exception as exc:
            current = repo.get_artifact(report_id, artifact_id)
            if current and current.get("response_id"):
                logger.exception("Touch presentation accepted; recover by refresh.")
                return public(current)
            definite = isinstance(exc, APIStatusError) and 400 <= exc.status_code < 500 and exc.status_code != 408
            logger.exception("Touch presentation submission failed or uncertain.")
            job = {"status": "failed" if definite else "SUBMISSION_UNKNOWN", "error": {"message":
                "Demande refusée par le fournisseur." if definite else
                "Acceptation non confirmée. Ne relancez pas : rattachez le resp_ des logs puis actualisez."}}
        return public(repo.save_job(report_id, artifact_id, job))


def list_presentations(report_id, limit=30, offset=0):
    _required_report(report_id)
    return repo.list_artifacts(report_id, limit, offset)


def get_presentation(report_id, artifact_id):
    _required_report(report_id)
    item = repo.get_artifact(report_id, artifact_id)
    if not item:
        raise LookupError("Présentation introuvable.")
    return public(item)


def refresh_presentation(report_id, artifact_id, response_id=None):
    _required_report(report_id)
    item = repo.get_artifact(report_id, artifact_id)
    if not item:
        raise LookupError("Présentation introuvable.")
    if item["status"] == "completed":
        return public(item)
    if response_id and item.get("response_id") and response_id != item["response_id"]:
        raise ValueError("Une autre réponse est déjà associée à cette présentation.")
    result = item.get("result") or {}
    if item["status"] == "validation_failed" and result.get("text"):
        job = dict(result)
        try:
            job.update(validate_result(job["text"], item["request"]))
            job.update(status="completed", error=None)
        except (ValueError, KeyError, IndexError) as exc:
            job.update(status="validation_failed", error={"message": str(exc)})
    else:
        response_id = response_id or item.get("response_id")
        if not response_id:
            return public(item)
        if not response_id.startswith("resp_"):
            raise ValueError("Identifiant de réponse invalide.")
        with client() as connection:
            response = connection.responses.retrieve(response_id)
        job = _serialize(response, item)
    return public(repo.save_job(report_id, artifact_id, job))
