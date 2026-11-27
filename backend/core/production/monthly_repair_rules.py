"""Only unambiguous, existing text locations may be repaired in place."""
import copy
import re

REPAIR_KIND = "MONTHLY_TARGETED_REPAIR"
AUDIT_REVISION = "monthly-page-audit-v1"


def repair_targets(document, issues):
    if not issues:
        return []
    targets = []
    pages = document.get("pages") or []
    for issue in issues:
        location = (issue.get("location") or "").strip()
        # Legacy cross-page reviews sometimes use an explicit page identifier
        # instead of the canonical array index. Resolve only a unique exact ID.
        alias = re.fullmatch(r"pages\[([^\]]+)\]\.(paragraphs|bullets|cautions|metrics)\[(\d+)\]", location)
        if alias:
            page_id, field, offset = alias.groups()
            matches = [index for index, page in enumerate(pages) if page.get("page_id") == page_id]
            if len(matches) != 1:
                return []
            location = f"/pages/{matches[0]}/{field}/{offset}"
        machine = re.fullmatch(r"/pages/(\d+)/(paragraphs|bullets|cautions|metrics)/(\d+)", location)
        scalar = re.fullmatch(r"/pages/(\d+)/(title|eyebrow|takeaway)", location)
        if machine or scalar:
            groups = (machine or scalar).groups()
            page_index, field = int(groups[0]), groups[1]
            if page_index >= len(pages):
                return []
            values = pages[page_index].get(field)
            if machine:
                if not isinstance(values, list) or int(groups[2]) >= len(values):
                    return []
            elif not isinstance(values, str):
                return []
            if location not in targets:
                targets.append(location)
            continue
        metric = re.fullmatch(r"\s*([^\s·:,]+)[\s·:,]+(?:metric|métrique)\s+[«\"](.+?)[»\"]\s*", location, re.IGNORECASE)
        if metric:
            found = [(i, offset) for i, page in enumerate(pages) if page.get("page_id") == metric[1]
                     for offset, item in enumerate(page.get("metrics") or [])
                     if item.get("label", "").strip().casefold() == metric[2].strip().casefold()]
            if len(found) != 1:
                return []
            pointer = f"/pages/{found[0][0]}/metrics/{found[0][1]}"
            if pointer not in targets:
                targets.append(pointer)
            continue
        # Do not guess a destination from a prose explanation or source ID.
        match = re.fullmatch(
            r"\s*([^\s·:,]+)[\s·:,]+(paragraph|paragraphe|bullet|puce)\s+(\d+)(?:\s*\([^\n]*\))?\s*",
            location, re.IGNORECASE,
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
    removals = []
    for pointer in targets:
        match = re.fullmatch(r"/pages/(\d+)/(paragraphs|bullets|cautions|metrics)/(\d+)", pointer)
        scalar = re.fullmatch(r"/pages/(\d+)/(title|eyebrow|takeaway)", pointer)
        value = replacements[pointer]
        if scalar:
            if not isinstance(value, str) or not value.strip():
                raise ValueError("Le texte corrigé doit être non vide.")
            index, field = scalar.groups()
            changed |= result["pages"][int(index)][field] != value
            result["pages"][int(index)][field] = value
            continue
        if not match:
            raise ValueError("Passage de correction invalide.")
        index, field, offset = match.groups()
        if field == "metrics":
            if value is not None:
                raise ValueError("Une métrique signalée peut seulement être retirée, jamais réinventée.")
            removals.append((int(index), int(offset)))
            changed = True
            continue
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Le passage corrigé doit être un texte non vide.")
        old = result["pages"][int(index)][field][int(offset)]
        result["pages"][int(index)][field][int(offset)] = value
        changed |= old != value
    for index, offset in sorted(removals, reverse=True):
        del result["pages"][index]["metrics"][offset]
        if not result["pages"][index]["metrics"] and result["pages"][index]["layout"] == "METRICS":
            result["pages"][index]["layout"] = "ANALYSIS"
    if not changed:
        raise ValueError("La correction ne modifie aucun passage signalé.")
    return result
