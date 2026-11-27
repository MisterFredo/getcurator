"""Single-reference citations: only the server writes paths and verbatim quotes."""
import copy
import hashlib
import json
from core.production.digest_source import EVIDENCE_FIELDS
from core.production.citation_resolution import CitationValidationError

CATALOG_MODE = "FROZEN_EVIDENCE_CATALOG_V1"

CATALOG_INSTRUCTIONS = """
PROTOCOLE DE CITATION DU MONTHLY
evidence_catalog.contents identifie les contenus, dates et rôles mensuels.
evidence_catalog.passages fournit des témoins exacts et un evidence_index.
Pour chaque source S1, S2..., renvoie uniquement id et evidence_index.
Ce protocole remplace les consignes de saisie manuelle des champs de sources.
Choisis le passage qui soutient réellement le constat, ses chiffres, son
périmètre et son statut. Le serveur fournit ensuite chemin, version, content_id,
libellé et citation exacte : ne réécris pas ces champs et ne les invente pas.
Les pages et leurs indicateurs citent toujours les identifiants S1, S2...
Plusieurs passages d'un même contenu ne sont pas des confirmations indépendantes.
Les résumés, le profil et les titres sont du contexte, pas des preuves citables.
Une référence techniquement valide ne prouve pas une interprétation : conserve
les réserves et cite séparément les développements distincts sur chaque page.
""".strip()


def _chunks(text):
    start = 0
    while start < len(text):
        end = min(start + 1200, len(text))
        if end < len(text):
            boundary = text.rfind(" ", start + 800, end)
            if boundary > start:
                end = boundary + 1
        chunk = text[start:end]
        if chunk.strip():
            yield chunk
        start = end


def build_catalog(corpus):
    entries, contents = [], []
    # Deduplicate identical witnesses of the same content in the same monthly
    # role. The first frozen snapshot retains exact provenance.
    seen = set()
    for snapshot in corpus.reports:
        report = snapshot.payload
        if report.get("source_type") != "DIGEST_SUBJECT":
            continue
        role = report.get("monthly_period_role")
        metadata = {item["content_id"]: item for item in report.get("sources", [])}
        for index, content in enumerate(report.get("contents", [])):
            cid = content["content_id"]
            content_ref = f"C{len(contents) + 1}"
            meta = metadata.get(cid) or {}
            contents.append({"content_ref": content_ref, "content_id": cid, "monthly_period_role": role,
                "title": content.get("title"), "publication_day": content.get("publication_day"),
                "published_at": content.get("published_at"), "source_name": meta.get("source_name")})
            label = meta.get("title") or content.get("title") or report.get("subject") or cid
            for field in EVIDENCE_FIELDS:
                value = content.get(field)
                values = (list(enumerate(value)) if isinstance(value, list) else []) if field == "chiffres" else [(None, value)]
                for number_index, text in values:
                    if not isinstance(text, str) or not text.strip():
                        continue
                    pointer = f"/contents/{index}/{field}" + (f"/{number_index}" if number_index is not None else "")
                    for chunk in _chunks(text):
                        key = (role, cid, field, chunk)
                        if key in seen:
                            continue
                        seen.add(key)
                        entries.append({"evidence_index": len(entries), "content_ref": content_ref,
                            "field": field, "text": chunk,
                            "source": {"report_id": snapshot.report_id, "report_version": snapshot.version_number,
                                       "json_pointer": pointer, "quote": chunk, "content_id": cid, "label": str(label)[:300]}})
    if not entries:
        raise ValueError("Le Monthly ne fournit aucun passage analytique citable.")
    payload = {"contents": contents, "entries": entries}
    digest = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True,
                                      separators=(",", ":")).encode("utf-8")).hexdigest()
    return {**payload, "catalog_sha256": digest}


def payload_for_model(payload, catalog):
    result = copy.deepcopy(payload)
    for report in result["saved_reports"]:
        if report.get("source_type") == "DIGEST_SUBJECT":
            report.pop("contents", None)
            report.pop("sources", None)
    result["evidence_catalog"] = {"contents": catalog["contents"],
        "passages": [{key: entry[key] for key in ("evidence_index", "content_ref", "field", "text")}
                     for entry in catalog["entries"]]}
    return result


def wire_schema(document_schema, catalog):
    schema = copy.deepcopy(document_schema)
    original = schema["$defs"]["DocumentSource"]["properties"]["id"]
    schema["$defs"]["DocumentSource"] = {"type": "object", "properties": {
        "id": original, "evidence_index": {"type": "integer", "minimum": 0, "maximum": len(catalog["entries"]) - 1}},
        "required": ["id", "evidence_index"], "additionalProperties": False}
    return schema


def hydrate_sources(document, catalog):
    result = copy.deepcopy(document)
    sources = result.get("sources")
    if not isinstance(sources, list):
        raise ValueError("Liste des références du document absente.")
    hydrated, issues = [], []
    for position, source in enumerate(sources):
        try:
            if not isinstance(source, dict) or set(source) != {"id", "evidence_index"}:
                raise ValueError("La référence doit contenir uniquement id et evidence_index.")
            index = source["evidence_index"]
            if type(index) is not int or not 0 <= index < len(catalog["entries"]):
                raise ValueError("Référence absente du catalogue de preuves figé.")
            hydrated.append({"id": source["id"], **catalog["entries"][index]["source"]})
        except (ValueError, KeyError, TypeError) as exc:
            issues.append({"code": "CITATION", "location": f"sources[{position}]", "message": str(exc)})
    if issues:
        raise CitationValidationError(issues)
    result["sources"] = hydrated
    return result
