"""Admin-edited text revisions, frozen evidence, mandatory independent review.

No provider call, no corpus update and no override of an assessment. Manual
edits are explicit DOCUMENT artifacts, distinct from automatic repair attempts.
"""
import copy
import hashlib
import json
from uuid import NAMESPACE_URL, uuid5

from core.production import workflow_repository as repo, workflow_service as workflow, monthly_state as state
from core.production.document_models import ProductionDocument
from core.production.document_service import load_corpus, validate_against_corpus
from core.production.monthly_repair_rules import AUDIT_REVISION
from core.production.monthly_repair_contract import EDITORIAL_EDIT_KIND, repair_plan, apply_repair
from core.production.monthly_retry_policy import document_budget


def _hash(value):
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _current(production_id):
    corpus = load_corpus(production_id)
    if not corpus.request.monthly_user:
        raise ValueError("Cette production n’est pas un Monthly User.")
    rows = sorted(state.history(production_id), key=lambda r: r["version_number"], reverse=True)
    # Compare the scoped cache with the authoritative repository head before
    # accepting a new editor context. Never edit an obsolete cached version.
    head = repo.list_artifacts(production_id, 1, 0)
    if not rows or not head or rows[0]["artifact_id"] != head[0]["artifact_id"]:
        raise workflow.WorkflowConflict("L’historique a changé. Rechargez le rapport avant de corriger.")
    if any(r["status"] in repo.ACTIVE for r in rows):
        raise workflow.WorkflowConflict("Une étape est en cours. Attendez sa fin avant de corriger.")
    document_row = next((r for r in rows if r["stage"] == "DOCUMENT"), None)
    if not document_row:
        raise LookupError("Aucun document enregistré à corriger.")
    parent = repo.get_artifact(production_id, document_row["artifact_id"])
    if not parent or parent["status"] != "completed" or parent["corpus_sha256"] != corpus.corpus_sha256:
        raise workflow.WorkflowConflict("Un document complet correspondant au socle est requis.")
    assessment = None
    for row in rows:
        if row["stage"] not in {"REVIEW", "REVIEW_BATCH"} or row["status"] != "completed":
            continue
        item = repo.get_artifact(production_id, row["artifact_id"])
        if (item and (item.get("request") or {}).get("document_artifact_id") == parent["artifact_id"]
                and item["request"].get("audit_revision") == AUDIT_REVISION
                and item["corpus_sha256"] == corpus.corpus_sha256):
            assessment = item
            break
    review = ((assessment or {}).get("result") or {}).get("review") or {}
    if review.get("passed") is not False or not review.get("issues"):
        raise workflow.WorkflowConflict("Un contrôle terminé avec des remarques est requis.")
    budget = document_budget(rows, lambda row: repo.get_artifact(production_id, row["artifact_id"]))
    if budget["can_correct"]:
        raise workflow.WorkflowConflict("Une correction automatique est encore disponible. Reprenez son suivi.")
    document = parent["result"]["document"]
    plan = repair_plan(document, review["issues"])
    token = _hash({"production_id": production_id, "corpus_sha256": corpus.corpus_sha256,
                   "document_artifact_id": parent["artifact_id"], "review_artifact_id": assessment["artifact_id"],
                   "document": document, "review": review})
    return corpus, parent, assessment, document, review, plan, token


def editorial_context(production_id):
    with state.pipeline_scope(production_id):
        corpus, parent, assessment, document, review, plan, token = _current(production_id)
        sources = {s["id"]: s for s in document["sources"]}
        fields = []
        for path in plan["targets"]:
            index = int(path.split("/")[2])
            page = document["pages"][index]
            fields.append({"location": path, "page_id": page["page_id"], "page_number": index + 1,
                           "page_title": page["title"], "value": plan["before_values"][path],
                           "max_length": {"title": 160, "eyebrow": 80, "takeaway": 450}.get(path.split("/")[3], 2200),
                           "issues": [i for i in review["issues"] if i["location"] == path],
                           "sources": [copy.deepcopy(sources[sid]) for sid in dict.fromkeys(page["source_ids"]) if sid in sources]})
        return {"production_id": production_id, "document_artifact_id": parent["artifact_id"],
                "review_artifact_id": assessment["artifact_id"], "corpus_sha256": corpus.corpus_sha256,
                "context_sha256": token, "document_title": document["title"],
                "language": corpus.request.output_language,
                "editable": bool(plan["targets"] and not plan["unhandled_locations"]),
                "unhandled_locations": plan["unhandled_locations"], "fields": fields}


def save_editorial_edit(production_id, payload, actor_user_id):
    if not actor_user_id:
        raise ValueError("L’auteur de la correction doit être identifié.")
    body = payload.model_dump(mode="json")
    artifact_id = str(uuid5(NAMESPACE_URL, f"monthly-editorial-edit/{production_id}/{body['request_id']}"))
    request = {"kind": EDITORIAL_EDIT_KIND, "document_artifact_id": body["document_artifact_id"],
               "review_artifact_id": body["review_artifact_id"], "actor_user_id": actor_user_id,
               "submission": body}
    with state.pipeline_scope(production_id):
        # Retry with the same ID/body after a lost HTTP reply returns the saved
        # operation even if its review has already started or finished.
        existing = repo.get_artifact(production_id, artifact_id)
        if existing:
            if (existing["stage"] != "DOCUMENT" or existing.get("request") != request
                    or existing["corpus_sha256"] != body["corpus_sha256"]):
                raise workflow.WorkflowConflict("Cet identifiant désigne une autre correction. Rechargez le rapport.")
            state.remember(existing)
            return existing
        corpus, parent, assessment, document, review, plan, token = _current(production_id)
        if (body["document_artifact_id"] != parent["artifact_id"]
                or body["review_artifact_id"] != assessment["artifact_id"]
                or body["corpus_sha256"] != corpus.corpus_sha256 or body["context_sha256"] != token):
            raise workflow.WorkflowConflict("Le document ou son contrôle a changé. Rechargez les passages avant de les enregistrer.")
        if plan["unhandled_locations"] or not plan["targets"]:
            raise ValueError("Toutes les remarques doivent viser des champs texte corrigeables.")
        candidate = apply_repair(document, plan, body["replacements"], body["evidence_bindings"])
        validated = validate_against_corpus(ProductionDocument.model_validate(copy.deepcopy(candidate)), corpus)
        if validated.model_dump(mode="json") != candidate:
            raise ValueError("La validation modifierait des champs hors correction.")
        # Complete artifact and request are saved atomically through the existing
        # reservation API; a crash cannot leave an unsubmitted LLM job here.
        result = {"status": "completed", "document": candidate, "origin": EDITORIAL_EDIT_KIND,
                  "document_artifact_id": artifact_id, "parent_document_artifact_id": parent["artifact_id"],
                  "repaired_paths": plan["targets"], "before_values": plan["before_values"],
                  "evidence_bindings": body["evidence_bindings"], "reason": body["reason"],
                  "actor_user_id": actor_user_id, "error": None, "model": None, "usage": None}
        item, created = repo.reserve_artifact(
            production_id, artifact_id, "DOCUMENT", corpus.corpus_sha256, request,
            parent_id=parent["artifact_id"], ready_result=result,
        )
        if not created and (item.get("request") != request or item["status"] != "completed"):
            raise workflow.WorkflowConflict("La correction n’a pas pu être confirmée. Rechargez son historique.")
        state.remember(item)
        return item
