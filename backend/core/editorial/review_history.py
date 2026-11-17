import json
import re
import unicodedata
from uuid import uuid4

from core.editorial.repository import PREFIX, _rows

TABLE = f"{PREFIX}_WEEKLY_REVIEW"


def save_review(result):
    review_id = str(uuid4())
    _rows(f"""
        INSERT INTO `{TABLE}` (REVIEW_ID, WEEK_START, WEEK_END, CREATED_AT, RESULT_JSON)
        VALUES (@id, DATE(@start), DATE(@end), CURRENT_TIMESTAMP(), PARSE_JSON(@result))
    """, {
        "id": review_id, "start": result["start"], "end": result["end"],
        "result": json.dumps(result, ensure_ascii=False),
    })
    return {"id": review_id, **result}


def list_reviews(limit, offset):
    return _rows(f"""
        SELECT REVIEW_ID AS id, CAST(WEEK_START AS STRING) AS start,
               CAST(WEEK_END AS STRING) AS end, CAST(CREATED_AT AS STRING) AS created_at,
               ARRAY_LENGTH(JSON_QUERY_ARRAY(RESULT_JSON, '$.dossiers')) AS dossier_count
        FROM `{TABLE}`
        ORDER BY WEEK_END DESC, CREATED_AT DESC, REVIEW_ID DESC
        LIMIT @limit OFFSET @offset
    """, {"limit": limit, "offset": offset})


def read_review(review_id):
    rows = _rows(f"""
        SELECT CAST(CREATED_AT AS STRING) AS created_at, TO_JSON_STRING(RESULT_JSON) AS result
        FROM `{TABLE}` WHERE REVIEW_ID = @id
        LIMIT 1
    """, {"id": review_id})
    if not rows:
        return None
    return {"id": review_id, "created_at": rows[0]["created_at"], **json.loads(rows[0]["result"])}


def public_review(review):
    return {key: value for key, value in review.items() if key != "corpus_ids"}


def _title_terms(title):
    ascii_title = unicodedata.normalize("NFKD", title.casefold()).encode("ascii", "ignore").decode()
    return set(re.findall(r"[a-z0-9]{3,}", ascii_title))


def _contents(dossier):
    return {item["id"]: item for item in dossier["contents"]}


def _match(old, current, current_contents):
    old_ids = _contents(old).keys()
    old_terms = _title_terms(old["title"])
    ranks = []
    for index, dossier in enumerate(current):
        new_ids = current_contents[index].keys()
        overlap = len(old_ids & new_ids)
        terms = _title_terms(dossier["title"])
        title_score = len(old_terms & terms) / max(1, len(old_terms | terms))
        coverage = overlap / max(1, len(old_ids))
        if overlap and (coverage >= 0.5 or (overlap >= 2 and title_score >= 0.35)):
            ranks.append(((2, coverage, overlap, title_score), index, "contents"))
        elif title_score >= 0.8 and len(old_terms & terms) >= 3:
            ranks.append(((1, title_score, 0, 0), index, "title"))
    ranks.sort(reverse=True)
    if not ranks:
        return None, "unmatched"
    if len(ranks) > 1 and ranks[0][0][:3] == ranks[1][0][:3]:
        return None, "ambiguous"
    return ranks[0][1], ranks[0][2]


def compare_reviews(previous, current):
    current_corpus = set(current["corpus_ids"])
    previous_corpus = set(previous["corpus_ids"])
    successors = current["dossiers"]
    current_contents = [_contents(dossier) for dossier in successors]
    predecessors = {}
    unmatched = []
    for old in previous["dossiers"]:
        index, method = _match(old, successors, current_contents)
        if index is None:
            old_ids = _contents(old).keys()
            unmatched.append({
                "title": old["title"], "status": old["status"], "match": method,
                "still_in_corpus": len(old_ids & current_corpus),
                "outside_current_corpus": len(old_ids - current_corpus),
            })
        else:
            predecessors.setdefault(index, []).append((old, method))

    changes = []
    for index, dossier in enumerate(successors):
        prior = predecessors.get(index, [])
        old_ids = {content_id for old, _ in prior for content_id in _contents(old)}
        contents = current_contents[index]
        added = [
            {**item, "new_to_window": content_id not in previous_corpus}
            for content_id, item in contents.items() if content_id not in old_ids
        ]
        removed = old_ids - contents.keys()
        if not prior:
            kind = "new"
        elif len(prior) > 1:
            kind = "merged"
        elif added or removed or dossier["status"] != prior[0][0]["status"]:
            kind = "updated"
        else:
            kind = "stable"
        changes.append({
            "title": dossier["title"], "kind": kind, "status": dossier["status"],
            "previous": [
                {"title": old["title"], "status": old["status"], "match": method}
                for old, method in prior
            ],
            "added": added,
            "removed_from_dossier": len(removed),
            "development": dossier["development"],
        })
    return {"changes": changes, "unmatched": unmatched}
