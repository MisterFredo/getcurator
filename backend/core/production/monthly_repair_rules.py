"""Only unambiguous, existing text locations may be repaired in place."""
import copy
import re

REPAIR_KIND = "MONTHLY_TARGETED_REPAIR"


def repair_targets(document, issues):
    if not issues:
        return []
    targets = []
    pages = document.get("pages") or []
    for issue in issues:
        # Do not guess a destination from a prose explanation or source ID.
        match = re.fullmatch(
            r"\s*([^\s·:,]+)[\s·:,]+(paragraph|paragraphe|bullet|puce)\s+(\d+)\s*",
            issue.get("location") or "", re.IGNORECASE,
        )
        if not match:
            return []
        page_id, field, number = match.groups()
        matches = [i for i, page in enumerate(pages) if page.get("page_id") == page_id]
        if len(matches) != 1:
            return []
        index = matches[0]
        field = "paragraphs" if field.lower() in {"paragraph", "paragraphe"} else "bullets"
        offset = int(number) - 1
        texts = pages[index].get(field) or []
        if offset < 0 or offset >= len(texts) or not isinstance(texts[offset], str):
            return []
        pointer = f"/pages/{index}/{field}/{offset}"
        if pointer not in targets:
            targets.append(pointer)
    return targets


def apply_repair(document, replacements, targets):
    if not isinstance(replacements, dict) or set(replacements) != set(targets) or not targets:
        raise ValueError("La correction doit viser exactement les passages autorisés.")
    result = copy.deepcopy(document)
    changed = False
    for pointer in targets:
        match = re.fullmatch(r"/pages/(\d+)/(paragraphs|bullets)/(\d+)", pointer)
        if not match:
            raise ValueError("Passage de correction invalide.")
        value = replacements[pointer]
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Le passage corrigé doit être un texte non vide.")
        index, field, offset = match.groups()
        old = result["pages"][int(index)][field][int(offset)]
        result["pages"][int(index)][field][int(offset)] = value
        changed |= old != value
    if not changed:
        raise ValueError("La correction ne modifie aucun passage signalé.")
    return result
