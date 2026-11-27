"""Resolve Digest array positions by frozen content identity, never by wording."""
import re

_PATH = re.compile(
    r"/contents/(?:0|[1-9][0-9]*)/"
    r"(excerpt|signal_analytique|mecanique_expliquee|enjeu_strategique|point_de_friction|chiffres)"
    r"(?:/((?:0|[1-9][0-9]*)))?"
)


class CitationValidationError(ValueError):
    def __init__(self, issues):
        self.issues = issues
        super().__init__(f"Contrôles techniques non satisfaits ({len(issues)}) : " + " ; ".join(issue["message"] for issue in issues))


def resolve_digest_pointer(source, report):
    if report.get("source_type") != "DIGEST_SUBJECT":
        return None
    match = _PATH.fullmatch(source.json_pointer)
    if not match or (match[1] == "chiffres") != (match[2] is not None):
        raise ValueError(f"Source {source.id} : chemin analytique Digest invalide.")
    matches = [index for index, content in enumerate(report.get("contents") or [])
               if source.content_id and content.get("content_id") == source.content_id]
    if len(matches) != 1:
        raise ValueError(f"Source {source.id} : contenu absent ou ambigu dans le rapport cité.")
    pointer = f"/contents/{matches[0]}/{match[1]}"
    if match[2] is not None:
        pointer += f"/{match[2]}"
    if pointer == source.json_pointer:
        return None
    note = {"source_id": source.id, "content_id": source.content_id,
            "old_pointer": source.json_pointer, "resolved_pointer": pointer}
    source.json_pointer = pointer
    return note


def prepare_digest_citations(sources, reports, materialize=False, normalizations=None):
    """Legacy Monthly quotes become explicit frozen-field witnesses.

    This does not validate the page's interpretation. Monthly semantic review
    remains mandatory before exposing a finished report.
    """
    issues = []
    for source in sources:
        try:
            report = reports.get((source.report_id, source.report_version))
            if report is None:
                raise ValueError(f"Source {source.id} : rapport ou version inconnus.")
            if report.get("source_type") != "DIGEST_SUBJECT":
                continue
            note = resolve_digest_pointer(source, report)
            if note and normalizations is not None:
                normalizations.append(note)
            match = _PATH.fullmatch(source.json_pointer)
            index = int(source.json_pointer.split("/")[2])
            value = report["contents"][index][match[1]]
            if match[2] is not None:
                value = value[int(match[2])]
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Source {source.id} : passage analytique vide ou non textuel.")
            if source.quote in value:
                continue
            if materialize and len(value) <= 1200:
                old_quote = source.quote
                source.quote = value
                if normalizations is not None:
                    normalizations.append({"source_id": source.id, "content_id": source.content_id,
                        "kind": "FROZEN_PASSAGE_MATERIALIZED", "resolved_pointer": source.json_pointer,
                        "discarded_model_quote": old_quote,
                        "note": "Le témoin exact remplace la citation du modèle ; sa pertinence reste à contrôler éditorialement."})
            else:
                raise ValueError(f"Source {source.id} : citation absente du passage référencé"
                                 + (" ; passage long nécessitant une sélection dans le catalogue." if materialize else "."))
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            issues.append({"code": "CITATION", "location": f"sources.{source.id}", "message": str(exc)})
    if issues:
        raise CitationValidationError(issues)
