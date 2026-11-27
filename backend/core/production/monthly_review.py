import json
import os
import re
from core.production import workflow_repository as repo, workflow_service as workflow
from core.production.document_service import client, load_corpus, pointer_value
from core.production.monthly_models import MonthlyQualityReview
from core.production.monthly_prompt import REVIEW_INSTRUCTIONS

REVIEW_WORKFLOW = "getcurator_monthly_quality_v1"


def deterministic_issues(document, corpus):
    issues = []
    metadata = corpus.request.monthly_user
    reports = {(r.report_id, r.version_number): r.payload for r in corpus.reports}
    for source in document["sources"]:
        payload = reports.get((source["report_id"], source["report_version"]), {})
        if payload.get("source_type") != "DIGEST_SUBJECT":
            issues.append({"code": "CITATION", "location": source["id"],
                           "message": "Citer un contenu lié, pas le rapport de référence ni le profil."})
    for page_index, page in enumerate(document["pages"]):
        for metric_index, metric in enumerate(page["metrics"]):
            label = metric["label"].lower()
            source = next((s for s in document["sources"] if s["id"] == metric["source_id"]), None)
            year_as_count = False
            if source and "/chiffres/" in source["json_pointer"]:
                report = reports.get((source["report_id"], source["report_version"]))
                if report:
                    value = pointer_value(report, source["json_pointer"])
                    parts = [part.strip().lower() for part in value.split("|")]
                    year_as_count = (len(parts) >= 3 and parts[2] in {"ans", "year", "years", "année", "années"}
                                     and 1900 <= metric["value"] <= 2100)
            if year_as_count or re.search(r"\b(year|année|launch date|date de lancement|rollout date)\b", label):
                issues.append({"code": "NUMBER", "location": f"/pages/{page_index}/metrics/{metric_index}",
                               "message": "Une date ou année n’est pas un KPI ; conserver le repère dans le texte."})
    all_text = " ".join([document["title"], document["subtitle"]] + [
        text for p in document["pages"] for text in
        [p["title"], p["eyebrow"], *p["paragraphs"], *p["bullets"], p["takeaway"], *p["cautions"]]
    ]).lower()
    if metadata["provisional"] and not re.search(r"provisional|provisoire", all_text):
        issues.append({"code": "PERIOD", "location": "cover",
                       "message": "Identifier clairement le rapport comme provisoire."})
    return issues


def review_input(document, corpus):
    reports = {(r.report_id, r.version_number): r.payload for r in corpus.reports}
    cited = []
    for source in document["sources"]:
        report = reports[(source["report_id"], source["report_version"])]
        content = next((c for c in report.get("contents", [])
                        if c["content_id"] == source.get("content_id")), None)
        cited.append({"source": source, "monthly_period_role": report.get("monthly_period_role"),
                      "exact_passage": pointer_value(report, source["json_pointer"]), "content_context": content})
    previous = [r.payload for r in corpus.reports if r.payload.get("source_type") == "MONTHLY_REFERENCE"]
    return {"brief": corpus.request.model_dump(mode="json"), "document": document,
            "cited_evidence": cited, "previous_report_context": previous,
            "deterministic_issues": deterministic_issues(document, corpus)}


def _serialize(response, document_artifact_id):
    status = response.status
    error = response.error.model_dump(mode="json") if response.error else None
    review = None
    if status == "completed":
        try:
            review = MonthlyQualityReview.model_validate_json(response.output_text or "")
            if review.passed != (not review.issues):
                raise ValueError("Contrôle qualité incohérent : passed ne correspond pas aux anomalies.")
            review = review.model_dump(mode="json")
        except ValueError as exc:
            status = "validation_failed"
            error = {"message": str(exc)}
    return {"id": response.id, "status": status, "model": response.model,
            "text": response.output_text or "", "review": review,
            "document_artifact_id": document_artifact_id, "error": error,
            "production_id": (response.metadata or {}).get("production_id"),
            "corpus_sha256": (response.metadata or {}).get("corpus_sha256"),
            "usage": response.usage.model_dump(mode="json") if response.usage else None}


def start_review(production_id, artifact_id, document_artifact_id):
    corpus = load_corpus(production_id)
    document_artifact = repo.get_artifact(production_id, document_artifact_id)
    if not document_artifact or document_artifact["stage"] != "DOCUMENT" or document_artifact["status"] != "completed":
        raise ValueError("Document complet requis pour le contrôle qualité.")
    request = {"document_artifact_id": document_artifact_id}
    document = document_artifact["result"]["document"]
    issues = deterministic_issues(document, corpus)
    if issues:
        return repo.reserve_artifact(
            production_id, artifact_id, "REVIEW", corpus.corpus_sha256, request,
            parent_id=document_artifact_id,
            ready_result={"status": "completed", "document_artifact_id": document_artifact_id,
                          "review": {"passed": False, "issues": issues}},
        )[0]
    item, created = workflow._reserve(
        production_id=production_id, artifact_id=artifact_id, stage="REVIEW",
        corpus_sha256=corpus.corpus_sha256, request=request, parent_id=document_artifact_id,
    )
    if not created:
        return item
    def submit(accepted):
        with client() as connection:
            response = connection.responses.create(
                model=os.getenv("PRODUCTION_REVIEW_MODEL") or os.getenv("PRODUCTION_DOCUMENT_MODEL") or "gpt-5.4",
                instructions=REVIEW_INSTRUCTIONS,
                input=json.dumps(review_input(document, corpus), ensure_ascii=False, allow_nan=False),
                text={"format": {"type": "json_schema", "name": "monthly_quality_review", "strict": True,
                                  "schema": MonthlyQualityReview.model_json_schema()}},
                reasoning={"effort": "medium"}, max_output_tokens=8000, background=True, store=True,
                metadata={"workflow": REVIEW_WORKFLOW, "production_id": production_id,
                          "corpus_sha256": corpus.corpus_sha256, "artifact_id": artifact_id,
                          "document_artifact_id": document_artifact_id},
            )
        accepted(response)
        return _serialize(response, document_artifact_id)
    return workflow._submit(production_id, artifact_id, submit)


def refresh_review(production_id, artifact_id, response_id=None):
    item = repo.get_artifact(production_id, artifact_id)
    if not item or item["stage"] != "REVIEW":
        raise ValueError("Contrôle qualité introuvable.")
    if item["status"] == "completed":
        return item
    response_id = response_id or item.get("response_id")
    if not response_id:
        return item
    if item.get("response_id") and item["response_id"] != response_id:
        raise ValueError("Ce contrôle est déjà rattaché à une autre réponse.")
    with client() as connection:
        response = connection.responses.retrieve(response_id)
    metadata = response.metadata or {}
    if (metadata.get("workflow") != REVIEW_WORKFLOW or metadata.get("production_id") != production_id
            or metadata.get("corpus_sha256") != item["corpus_sha256"]
            or metadata.get("artifact_id") != artifact_id
            or metadata.get("document_artifact_id") != item["request"]["document_artifact_id"]):
        raise ValueError("La réponse ne correspond pas à ce contrôle qualité.")
    job = _serialize(response, item["request"]["document_artifact_id"])
    if job["status"] == item["status"] and job.get("id") == item.get("response_id") and job["status"] in repo.ACTIVE:
        return item
    return repo.save_job(production_id, artifact_id, job)
