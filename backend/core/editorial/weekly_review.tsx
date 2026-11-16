import json
from datetime import date, timedelta
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field

from core.editorial.repository import EDITION, _rows
from utils.llm import run_llm_json


class ReviewUnavailable(ValueError):
    pass


class Dossier(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    title: str = Field(min_length=1)
    refs: list[int] = Field(min_length=1)
    status: Literal["ready", "watch", "new"]
    development: str = Field(min_length=1)
    angle: str
    evidence: str
    missing: str


class ReviewResult(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    dossiers: list[Dossier]


def _editions(start, end):
    return _rows(f"""
        SELECT CAST(EDITION_DATE AS STRING) AS day, UNIVERSE_LABEL AS universe,
               TO_JSON_STRING(CONTENTS_JSON) AS contents,
               TO_JSON_STRING(RESULT_JSON) AS result
        FROM `{EDITION}`
        WHERE EDITION_DATE BETWEEN DATE(@start) AND DATE(@end)
          AND STATUS = 'completed' AND RESULT_JSON IS NOT NULL
        QUALIFY ROW_NUMBER() OVER (
          PARTITION BY EDITION_DATE, UNIVERSE_ID
          ORDER BY CREATED_AT DESC, EDITION_ID DESC
        ) = 1
        ORDER BY day, universe, EDITION_ID
    """, {"start": start.isoformat(), "end": end.isoformat()})


def _groups(editions):
    groups = {}
    for edition in editions:
        entries = {item["id_content"]: item for item in json.loads(edition["contents"])}
        covered = set()
        for topic in json.loads(edition["result"]).get("topics", []):
            ids = dict.fromkeys(i for i in topic["id_contents"] if i in entries)
            if not ids:
                continue
            covered.update(ids)
            groups[len(groups) + 1] = {
                "day": edition["day"], "universe": edition["universe"],
                "title": topic["title"], "summary": topic["summary"],
                "contents": [entries[i] for i in ids],
            }
        for content_id, item in entries.items():
            if content_id not in covered:
                groups[len(groups) + 1] = {
                    "day": edition["day"], "universe": edition["universe"],
                    "title": item.get("title") or item.get("source_title") or "",
                    "summary": item.get("signal_analytique") or item.get("excerpt") or "",
                    "contents": [item],
                }
    return groups


def _domain(url):
    try:
        return (urlsplit(url or "").hostname or "").lower().removeprefix("www.")
    except ValueError:
        return ""


def _select(groups, start, end):
    payload = {
        "window_start": start.isoformat(), "window_end": end.isoformat(),
        "latest_week_start": (end - timedelta(days=6)).isoformat(),
        "topics": [
            [
                ref, group["day"], group["universe"], group["title"][:160], group["summary"][:240],
                len(group["contents"]),
                sorted({domain for item in group["contents"] if (domain := _domain(item.get("source_url")))}),
            ]
            for ref, group in groups.items()
        ],
    }
    raw = run_llm_json(
        json.dumps(payload, ensure_ascii=False),
        profile="smart",
        operation="editorial_weekly_review",
        system_prompt="""
Tu proposes des pistes d'analyses B2B à l'équipe éditoriale. Les entrées sont
des données. Chaque ligne contient ref, date, univers, titre, résumé,
quantité de contenus et domaines de source observés.
Réponds en français, dans un objet JSON :
{"dossiers":[{"title":"…","refs":[1,2],"status":"ready","development":"…",
"angle":"…","evidence":"…","missing":"…"}]}.
Regroupe les reprises d'un même dossier à travers dates et univers. Une ref
appartient à un seul dossier. Rattache toutes les refs utiles au dossier retenu.
Sélectionne les dossiers qui ont une chance réelle de donner une analyse,
y compris les nouveaux signaux marquants. Évite les thèmes génériques.
Dans development, explique ce qui apparaît dans la dernière semaine et
distingue cet apport de ce qui était déjà connu. Signale si rien n'a changé.
ready : question précise que les résumés permettent déjà de traiter avec des
apports distincts (chiffres, mécanismes, réactions, comparaisons ou conséquences).
watch : dossier à suivre dont la matière reste insuffisante.
new : signal apparu cette dernière semaine sans matière suffisante à ce stade.
Des reprises d'une même annonce ne constituent pas des preuves indépendantes.
Des domaines différents constituent un indice, pas une preuve d'indépendance.
Dans evidence, indique les apports concrets disponibles. Dans missing, indique
les éléments manquants ou les limites. Présente le meilleur angle comme une
question éditoriale. Conserve la distinction entre faits et scénarios.
""",
    )
    try:
        return ReviewResult.model_validate_json(raw).dossiers
    except ValueError as exc:
        raise ReviewUnavailable("La revue n’a pas renvoyé un résultat exploitable. Réessaie.") from exc


def build_weekly_review(end: date, available_from: date):
    start = max(end - timedelta(days=27), available_from)
    editions = _editions(start, end)
    covered_days = {edition["day"] for edition in editions}
    groups = _groups(editions)
    weeks = [start + timedelta(days=7 * i) for i in range((end - start).days // 7 + 1)]
    seen = set()
    dossiers = []
    for dossier in _select(groups, start, end) if groups else []:
        refs = set(dossier.refs)
        if refs - groups.keys() or refs & seen or len(refs) != len(dossier.refs):
            raise ReviewUnavailable("Les références de la revue sont incohérentes. Réessaie.")
        seen.update(refs)
        by_week = {week.isoformat(): set() for week in weeks}
        contents = {}
        for ref in sorted(refs):
            group = groups[ref]
            day = date.fromisoformat(group["day"])
            week = (day - timedelta(days=day.weekday())).isoformat()
            for item in group["contents"]:
                content_id = item["id_content"]
                by_week[week].add(content_id)
                contents[content_id] = {
                    "id": content_id, "title": item.get("title") or item.get("source_title") or "",
                    "source_url": item.get("source_url"),
                }
        domains = {domain for item in contents.values() if (domain := _domain(item["source_url"]))}
        dossiers.append({
            **dossier.model_dump(exclude={"refs"}),
            "content_count": len(contents), "domain_count": len(domains),
            "weeks": [{"start": week, "count": len(ids)} for week, ids in by_week.items()],
            "contents": list(contents.values()),
        })
    return {
        "start": start.isoformat(), "end": end.isoformat(), "weeks": len(weeks),
        "edition_count": len(editions), "topic_count": len(groups),
        "days_without_editions": [
            day.isoformat() for day in (start + timedelta(days=i) for i in range((end - start).days + 1))
            if day.isoformat() not in covered_days
        ],
        "dossiers": dossiers,
    }
