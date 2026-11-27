"""Page-scoped durable reviews, plus a separate cross-page coherence check.

Every page is checked before collecting a final assessment. Identical inputs
reuse their saved assessment; a repaired page never reopens an unchanged page.
"""
import hashlib
import json
import os
from uuid import NAMESPACE_URL, uuid5

from core.production import workflow_repository as repo, workflow_service as workflow
from core.production.document_service import client, load_corpus
from core.production.monthly_models import MonthlyQualityReview
from core.production.monthly_prompt import REVIEW_INSTRUCTIONS
from core.production.monthly_review import deterministic_issues, review_input
from core.production.monthly_repair_rules import AUDIT_REVISION

AUDIT_WORKFLOW = "getcurator_monthly_page_audit_v1"
AUDIT_STAGES = {"REVIEW_PAGE", "REVIEW_CROSS"}

PAGE_INSTRUCTIONS = REVIEW_INSTRUCTIONS + """
Tu contrôles une seule page, avec ses preuves et le mandat. Examine tous ses
paragraphes, puces, indicateurs, graphique et conclusion avant de répondre.
Signale ensemble tous les défauts matériels constatés, pas seulement le premier.
N'exige pas que cette page seule fasse la comparaison ou porte toutes les
réserves du rapport. Les contraintes de période et de comparaison sont vérifiées
dans un contrôle transversal séparé. Une couverture ou une page sources peut
ne pas citer de fait ; leur contenu factuel éventuel reste contrôlé.
Ne fusionne pas des mécanismes distincts simplement parce qu'ils partagent un
marché ou une entreprise. Pour un KPI, vérifie sa fonction dans l'argument.
Utilise exclusivement l'une des localisations machine fournies dans locations
pour chaque défaut. Pour un paragraphe ou une métrique, utilise la localisation
la plus précise. Les demandes de style ne sont pas des défauts matériels.
"""

CROSS_INSTRUCTIONS = REVIEW_INSTRUCTIONS + """
Contrôle uniquement la cohérence entre les pages : couverture temporelle,
comparaison entre périodes, répétitions matérielles, contradictions et synthèse
qui fusionne abusivement des développements distincts. Chaque page fait déjà
l'objet d'un contrôle factuel séparé : ne recommence pas l'évaluation locale
des KPI, citations ou formulations isolées. Les passages ne sont fournis ici
que pour vérifier une relation entre deux pages ou deux périodes.
Signale ensemble tous les défauts transversaux matériels et indique les pages
concernées. Si une correction peut se faire dans un champ précis, utilise sa
localisation machine. N'invente pas de comparaison faute de matière.
"""


def _hash(payload):
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode()).hexdigest()


def audit_requests(document, corpus):
    proof = review_input(document, corpus)
    brief = proof["brief"]
    jobs = []
    for index, page in enumerate(document["pages"]):
        refs = set(page["source_ids"])
        locations = [f"/pages/{index}/{field}" for field in ("title", "eyebrow", "takeaway", "layout", "chart")]
        for field in ("paragraphs", "bullets", "metrics", "cautions"):
            locations.extend(f"/pages/{index}/{field}/{offset}" for offset in range(len(page[field])))
        payload = {"brief": brief, "document_title": document["title"], "document_subtitle": document["subtitle"],
                   "page": page, "locations": locations,
                   "cited_evidence": [item for item in proof["cited_evidence"]
                                      if item["source"]["id"] in refs or (not refs and page["layout"] in {"COVER", "SUMMARY"})]}
        jobs.append(("REVIEW_PAGE", payload))
    cross = {"brief": brief, "document": document, "previous_report_context": proof["previous_report_context"],
             "locations": [location for _, payload in jobs for location in payload["locations"]]}
    jobs.append(("REVIEW_CROSS", cross))
    return jobs


def _serialize(response, request):
    status = response.status
    error = response.error.model_dump(mode="json") if response.error else None
    review = None
    if status == "completed":
        try:
            model = MonthlyQualityReview.model_validate_json(response.output_text or "")
            if model.passed != (not model.issues):
                raise ValueError("Contrôle incohérent : résultat et anomalies divergent.")
            review = model.model_dump(mode="json")
            if "locations" in request["payload"]:
                allowed = request["payload"]["locations"]
                if any(issue["location"] not in allowed for issue in review["issues"]):
                    raise ValueError("Le contrôle de page doit localiser chaque anomalie dans un champ existant.")
        except ValueError as exc:
            status, error = "validation_failed", {"message": str(exc)}
    return {"id": response.id, "status": status, "model": response.model,
            "text": response.output_text or "", "review": review, "error": error,
            "audit_revision": AUDIT_REVISION, "input_sha256": request["input_sha256"],
            "usage": response.usage.model_dump(mode="json") if response.usage else None}


def _start(production_id, corpus, stage, payload):
    input_hash = _hash({"revision": AUDIT_REVISION, "stage": stage, "payload": payload})
    artifact_id = str(uuid5(NAMESPACE_URL, f"monthly-audit/{production_id}/{input_hash}"))
    request = {"kind": AUDIT_REVISION, "stage": stage, "input_sha256": input_hash, "payload": payload}
    existing = repo.get_artifact(production_id, artifact_id)
    if existing:
        if existing["request"] != request or existing["corpus_sha256"] != corpus.corpus_sha256:
            raise ValueError("Le contrôle sauvegardé ne correspond pas à la page et à ses preuves.")
        return existing
    item, created = workflow._reserve(production_id=production_id, artifact_id=artifact_id,
        stage=stage, corpus_sha256=corpus.corpus_sha256, request=request)
    if not created:
        return item
    schema = MonthlyQualityReview.model_json_schema()
    if "locations" in payload:
        schema["$defs"]["MonthlyReviewIssue"]["properties"]["location"] = {
            "type": "string", "enum": payload["locations"],
        }
    def submit(accepted):
        with client() as connection:
            response = connection.responses.create(
                model=os.getenv("PRODUCTION_REVIEW_MODEL") or os.getenv("PRODUCTION_DOCUMENT_MODEL") or "gpt-5.4",
                instructions=PAGE_INSTRUCTIONS if stage == "REVIEW_PAGE" else CROSS_INSTRUCTIONS,
                input=json.dumps(payload, ensure_ascii=False, allow_nan=False),
                text={"format": {"type": "json_schema", "name": "monthly_page_review", "strict": True,
                                  "schema": schema}},
                reasoning={"effort": "medium"}, max_output_tokens=8000, background=True, store=True,
                metadata={"workflow": AUDIT_WORKFLOW, "production_id": production_id,
                          "corpus_sha256": corpus.corpus_sha256, "artifact_id": artifact_id,
                          "input_sha256": input_hash},
            )
        accepted(response)
        return _serialize(response, request)
    return workflow._submit(production_id, artifact_id, submit)


def start_audit(production_id, final_id, document_id):
    corpus = load_corpus(production_id)
    parent = repo.get_artifact(production_id, document_id)
    if (not parent or parent["stage"] != "DOCUMENT" or parent["status"] != "completed"
            or parent["corpus_sha256"] != corpus.corpus_sha256):
        raise ValueError("Document complet correspondant au socle requis.")
    document = parent["result"]["document"]
    issues = deterministic_issues(document, corpus)
    checks = []
    for stage, payload in audit_requests(document, corpus):
        item = _start(production_id, corpus, stage, payload)
        if item["status"] != "completed":
            return item
        checks.append(item["artifact_id"])
        issues.extend(item["result"]["review"]["issues"])
    # Aggregate every page, including pages with findings, before any repair.
    unique = []
    seen = set()
    for issue in issues:
        key = _hash(issue)
        if key not in seen:
            seen.add(key)
            unique.append(issue)
    return repo.reserve_artifact(
        production_id, final_id, "REVIEW", corpus.corpus_sha256,
        {"document_artifact_id": document_id, "audit_revision": AUDIT_REVISION, "check_artifact_ids": checks},
        parent_id=document_id, ready_result={"status": "completed", "document_artifact_id": document_id,
            "audit_revision": AUDIT_REVISION, "review": {"passed": not unique, "issues": unique}},
    )[0]


def refresh_audit(production_id, artifact_id, response_id=None):
    item = repo.get_artifact(production_id, artifact_id)
    if not item or item["stage"] not in AUDIT_STAGES:
        raise ValueError("Contrôle de page introuvable.")
    if item["status"] not in repo.ACTIVE:
        return item
    response_id = response_id or item.get("response_id")
    if not response_id:
        return item
    if item.get("response_id") and item["response_id"] != response_id:
        raise ValueError("Ce contrôle est déjà rattaché à une autre réponse.")
    with client() as connection:
        response = connection.responses.retrieve(response_id)
    expected = {"workflow": AUDIT_WORKFLOW, "production_id": production_id,
                "corpus_sha256": item["corpus_sha256"], "artifact_id": artifact_id,
                "input_sha256": item["request"]["input_sha256"]}
    if any((response.metadata or {}).get(k) != v for k, v in expected.items()):
        raise ValueError("La réponse ne correspond pas à ce contrôle de page.")
    job = _serialize(response, item["request"])
    if job["status"] in repo.ACTIVE and job["status"] == item["status"] and job["id"] == item.get("response_id"):
        return item
    return repo.save_job(production_id, artifact_id, job)
