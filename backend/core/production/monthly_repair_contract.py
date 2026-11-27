"""Generic, non-destructive text repair contract. No client-specific data."""
import copy
import re

EDITORIAL_EDIT_KIND = "MONTHLY_EDITORIAL_EDIT_V1"
REPAIR_MODE = "MONTHLY_SCOPED_TEXT_REPAIR_V1"
MAX_PAGE_REPAIRS = 3
MAX_REPAIR_PAGES = 4
MAX_REPAIR_FIELDS = 8
TEXT_FIELDS = {"paragraphs", "bullets", "cautions", "title", "eyebrow", "takeaway"}


def text_target(document, pointer):
    match = re.fullmatch(r"/pages/(\d+)/(paragraphs|bullets|cautions|title|eyebrow|takeaway)(?:/(\d+))?", pointer)
    if not match:
        raise ValueError("Un champ texte existant et précisément localisé est requis.")
    index, field, offset = match.groups()
    page = document["pages"][int(index)]
    if not isinstance(page.get("page_id"), str) or not page["page_id"]:
        raise ValueError("Identifiant de page absent.")
    value = page[field]
    if field in {"paragraphs", "bullets", "cautions"}:
        if offset is None or not isinstance(value, list):
            raise ValueError("Un index de texte est requis.")
        value = value[int(offset)]
    elif offset is not None:
        raise ValueError("Champ texte scalaire attendu.")
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Le texte à corriger doit exister et être non vide.")
    return page["page_id"], value


def repair_plan(document, issues):
    targets, before, page_ids, unhandled = [], {}, [], []
    ids = [p.get("page_id") for p in document.get("pages") or []]
    if len(ids) != len(set(ids)):
        return {"targets": [], "before_values": {}, "page_ids": [], "unhandled_locations": ["Identifiants de pages dupliqués"]}
    for issue in issues or []:
        pointer = issue.get("location") or ""
        try:
            page_id, value = text_target(document, pointer)
        except (ValueError, KeyError, IndexError, TypeError):
            unhandled.append(pointer or "Emplacement non précisé")
            continue
        page_index = int(pointer.split("/")[2])
        registered = {s["id"] for s in document.get("sources") or []}
        if not (registered & set(document["pages"][page_index].get("source_ids") or [])):
            unhandled.append(pointer + " : aucune preuve existante sur la page")
            continue
        if pointer not in targets:
            targets.append(pointer)
            before[pointer] = value
        if page_id not in page_ids:
            page_ids.append(page_id)
    if len(targets) > MAX_REPAIR_FIELDS or len(page_ids) > MAX_REPAIR_PAGES:
        unhandled.append("Périmètre trop large pour une correction ciblée")
    return {"targets": targets, "before_values": before, "page_ids": page_ids,
            "unhandled_locations": list(dict.fromkeys(unhandled))}


def apply_repair(document, plan, replacements, bindings):
    targets = plan["targets"]
    if (plan["unhandled_locations"] or not targets or not isinstance(replacements, dict)
            or not isinstance(bindings, dict) or set(replacements) != set(targets)
            or set(bindings) != set(targets)):
        raise ValueError("La correction doit viser exactement les champs signalés.")
    known = {s["id"] for s in document["sources"]}
    result = copy.deepcopy(document)
    for pointer in targets:
        page_id, old = text_target(document, pointer)
        if old != plan["before_values"][pointer] or page_id not in plan["page_ids"]:
            raise ValueError("Le document a changé depuis le diagnostic.")
        value = replacements[pointer]
        if not isinstance(value, str) or not value.strip() or value.strip() == old.strip():
            raise ValueError("Chaque passage signalé doit être corrigé par un texte non vide.")
        parts = pointer.split("/")
        index, field = int(parts[2]), parts[3]
        cited = set(document["pages"][index]["source_ids"])
        ids = bindings[pointer]
        if (not isinstance(ids, list) or not ids or any(not isinstance(i, str) for i in ids)
                or len(ids) != len(set(ids)) or set(ids) - (known & cited)):
            raise ValueError("Chaque correction doit citer des preuves existantes de sa page.")
        if len(parts) == 5:
            result["pages"][index][field][int(parts[4])] = value
        else:
            result["pages"][index][field] = value
    return result


def page_budget(history, read_artifact, current_document, repair_kind):
    """Count all legacy/current attempts by stable parent page IDs, not revisions.

    Failed/submission attempts count too. An expanded legacy page-wide target
    counts once for that page, even when only a subset was actually changed.
    Missing history is blocking, never treated as a zero counter.
    """
    lookup = {row["artifact_id"]: row for row in history}
    pages = {p["page_id"]: 0 for p in current_document.get("pages") or []}
    errors = []
    for row in history:
        if row["stage"] != "DOCUMENT":
            continue
        item = read_artifact(row)
        if not item:
            errors.append("Artefact historique introuvable")
            continue
        request = item.get("request") or {}
        if request.get("kind") != repair_kind:
            continue
        parent_row = lookup.get(request.get("document_artifact_id"))
        if not parent_row or not request.get("targets"):
            errors.append("Historique de correction incomplet")
            continue
        parent = (read_artifact(parent_row).get("result") or {}).get("document")
        if not parent:
            errors.append("Document parent d’une correction introuvable")
            continue
        touched = set()
        for pointer in request["targets"]:
            match = re.match(r"^/pages/(\d+)/", pointer)
            try:
                if not match:
                    raise ValueError("Emplacement historique non résolu")
                touched.add(parent["pages"][int(match[1])]["page_id"])
            except (IndexError, KeyError, ValueError, TypeError):
                errors.append("Emplacement historique non résolu")
        for page_id in touched:
            if page_id not in pages:
                errors.append("La structure des pages a changé dans l’historique")
            else:
                pages[page_id] += 1
    return {"attempts_by_page": pages, "errors": list(dict.fromkeys(errors))}
