"""Single deterministic fallback: retract flagged prose, never generate claims."""
import copy
import re

RETRACTION_MODE = "DETERMINISTIC_RETRACTION_V1"


def retraction_plan(document, issues):
    """Only one analysis page, exact citation/scope findings, surviving prose."""
    if not issues or len(issues) > 4:
        return None
    paths = []
    indexes = set()
    for issue in issues:
        if issue.get("code") not in {"CITATION", "SCOPE"}:
            return None
        path = issue.get("location") or ""
        match = re.fullmatch(r"/pages/(\d+)/(paragraphs/(\d+)|takeaway)", path)
        if not match:
            return None
        index = int(match[1])
        pages = document.get("pages") or []
        if index >= len(pages) or pages[index].get("layout") != "ANALYSIS":
            return None
        page = pages[index]
        if match[3] is not None:
            offset = int(match[3])
            if offset >= len(page.get("paragraphs") or []):
                return None
            value = page["paragraphs"][offset]
        else:
            value = page.get("takeaway")
        if not isinstance(value, str) or not value.strip():
            return None
        indexes.add(index)
        if path not in paths:
            paths.append(path)
    if len(indexes) != 1:
        return None
    index = next(iter(indexes))
    page = document["pages"][index]
    removed = {int(p.rsplit("/", 1)[1]) for p in paths if "/paragraphs/" in p}
    surviving = [text for i, text in enumerate(page["paragraphs"]) if i not in removed and text.strip()]
    if not surviving or not page.get("source_ids"):
        return None
    return {"targets": paths, "page_indexes": [index]}


def apply_retraction(document, issues):
    plan = retraction_plan(document, issues)
    if plan is None:
        raise ValueError("Le contrôle ne permet pas un retrait déterministe limité.")
    result = copy.deepcopy(document)
    # Array offsets always refer to the parent, never a partially modified list.
    for path in sorted(plan["targets"], key=lambda p: int(p.rsplit("/", 1)[1]) if "/paragraphs/" in p else -1, reverse=True):
        index = int(path.split("/")[2])
        if path.endswith("/takeaway"):
            result["pages"][index]["takeaway"] = ""
        else:
            del result["pages"][index]["paragraphs"][int(path.rsplit("/", 1)[1])]
    return result
