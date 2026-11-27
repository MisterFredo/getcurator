"""Resolve Digest array positions by frozen content identity, never by wording."""
import re

_PATH = re.compile(
    r"/contents/(?:0|[1-9][0-9]*)/"
    r"(excerpt|signal_analytique|mecanique_expliquee|enjeu_strategique|point_de_friction|chiffres)"
    r"(?:/((?:0|[1-9][0-9]*)))?"
)


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
