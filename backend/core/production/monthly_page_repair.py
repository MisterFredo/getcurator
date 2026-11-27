"""Server-owned page scope. Sources, structure and other pages remain frozen."""
import copy
import re

from core.production.monthly_repair_rules import repair_plan, canonicalize_sources
from core.production.monthly_repair_revision import PAGE_REPAIR_MODE

MAX_REPAIR_PAGES = 4
SCALARS = ("title", "eyebrow", "takeaway")
LISTS = ("paragraphs", "bullets", "cautions")


def page_repair_plan(document, issues):
    strict = repair_plan(document, issues)
    if strict["unhandled_locations"] or not strict["targets"]:
        return {**strict, "page_indexes": []}
    indexes = sorted({int(path.split("/")[2]) for path in strict["targets"]})
    pages = document.get("pages") or []
    # This operation must never become a whole-document rewrite.
    if len(indexes) > MAX_REPAIR_PAGES or len(indexes) >= len(pages):
        return {"targets": [], "page_indexes": [],
                "unhandled_locations": ["Périmètre trop large pour une correction locale."]}
    targets = []
    for index in indexes:
        page = pages[index]
        for field in SCALARS:
            if isinstance(page.get(field), str):
                targets.append(f"/pages/{index}/{field}")
        for field in LISTS:
            for offset, value in enumerate(page.get(field) or []):
                if isinstance(value, str):
                    targets.append(f"/pages/{index}/{field}/{offset}")
    # Metric deletion and exact alias canonicalization are still limited
    # to locations explicitly authorized by the existing audit rules.
    for pointer in strict["targets"]:
        if pointer not in targets:
            targets.append(pointer)
    return {"targets": targets, "page_indexes": indexes, "unhandled_locations": []}


def _value(document, pointer):
    value = document
    for token in pointer.strip("/").split("/"):
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def apply_page_repair(document, replacements, targets, bindings):
    if (not targets or not isinstance(replacements, dict)
            or not isinstance(bindings, dict)
            or set(replacements) != set(targets) or set(bindings) != set(targets)):
        raise ValueError("La correction doit couvrir exactement le périmètre autorisé.")
    known = {s["id"] for s in document.get("sources") or []}
    result = copy.deepcopy(document)
    changed_pages = set()
    scope_pages = set()
    removals = []
    canonicalize = False
    for pointer in targets:
        match = re.fullmatch(
            r"/pages/(\d+)/(title|eyebrow|takeaway|paragraphs|bullets|cautions|metrics|source_ids)(?:/(\d+))?",
            pointer,
        )
        if not match:
            raise ValueError("Chemin local invalide.")
        index, field, offset = match.groups()
        index = int(index)
        scope_pages.add(index)
        value, ids = replacements[pointer], bindings[pointer]
        if (not isinstance(ids, list)
                or any(not isinstance(s, str) or s not in known for s in ids)):
            raise ValueError("Preuve inconnue dans la correction.")
        old = _value(document, pointer)
        if field == "source_ids":
            if value is not None or ids:
                raise ValueError("La canonicalisation exige null et aucune preuve.")
            canonicalize = True
            continue
        if field == "metrics":
            if offset is None or value is not None or ids:
                raise ValueError("Seul le retrait de la métrique signalée est permis.")
            removals.append((index, field, int(offset)))
            changed_pages.add(index)
            continue
        if field in LISTS:
            if offset is None:
                raise ValueError("Indice de texte absent.")
            if value is None:
                if ids:
                    raise ValueError("Un passage retiré ne reçoit aucune preuve.")
                removals.append((index, field, int(offset)))
                changed_pages.add(index)
                continue
        elif offset is not None:
            raise ValueError("Indice interdit pour un titre ou une conclusion.")
        if not isinstance(value, str) or (not value.strip() and field != "eyebrow"):
            raise ValueError("Texte de remplacement invalide.")
        if value != old:
            if not ids:
                raise ValueError("Chaque texte modifié doit citer des preuves existantes.")
            changed_pages.add(index)
        if offset is None:
            result["pages"][index][field] = value
        else:
            result["pages"][index][field][int(offset)] = value
        # Evidence bindings may extend a page only using existing sources.
        before = result["pages"][index]["source_ids"]
        after = list(dict.fromkeys([*before, *ids]))
        if after != before:
            changed_pages.add(index)
            result["pages"][index]["source_ids"] = after
    for index, field, offset in sorted(removals, reverse=True):
        del result["pages"][index][field][offset]
        if field == "metrics" and not result["pages"][index]["metrics"]:
            if result["pages"][index]["layout"] == "METRICS":
                result["pages"][index]["layout"] = "ANALYSIS"
    if canonicalize:
        # Preserve the existing exact-alias action, but do not mutate other pages.
        canonical = copy.deepcopy(result)
        canonicalize_sources(canonical)
        for index in scope_pages:
            if canonical["pages"][index] != result["pages"][index]:
                changed_pages.add(index)
            result["pages"][index] = canonical["pages"][index]
        # Keep the complete source registry: other pages may still cite aliases.
    if changed_pages != scope_pages:
        raise ValueError("Chaque page signalée doit recevoir une correction effective.")
    if result["sources"] != document["sources"]:
        raise ValueError("Le registre des preuves est figé.")
    for index, page in enumerate(result["pages"]):
        if index not in scope_pages and page != document["pages"][index]:
            raise ValueError("Une page hors périmètre a changé.")
    return result
