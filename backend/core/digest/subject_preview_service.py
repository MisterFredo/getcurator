import json
import logging

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict, Field

from core.digest.candidate_service import _build_candidate, build_digest_candidate_context
from core.digest.repository import fetch_campaign
from core.editorial.repository import EDITION
from core.expertise.content_service import load_contents_by_ids
from core.expertise.profile_service import load_profile
from core.feedback.context_service import build_user_feedback_context
from core.user.user_preferences_service import get_user_preferences_detailed
from utils.bigquery_utils import query_bq
from utils.llm import run_llm_json

logger = logging.getLogger(__name__)
MUST_THRESHOLD = 85
NICE_THRESHOLD = 72


class PreviewUnavailable(ValueError):
    pass


class SubjectDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    refs: list[int] = Field(min_length=1)
    score: int = Field(ge=0, le=100)
    title: str = Field(min_length=1)
    development: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class SubjectSelection(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    subjects: list[SubjectDecision]


def _editions(start, end):
    return query_bq(sql=f"""
        SELECT CAST(EDITION_DATE AS STRING) AS day,
               UNIVERSE_LABEL AS universe,
               TO_JSON_STRING(CONTENTS_JSON) AS contents,
               TO_JSON_STRING(RESULT_JSON) AS result
        FROM `{EDITION}`
        WHERE EDITION_DATE >= DATE(@start) AND EDITION_DATE < DATE(@end)
          AND STATUS = 'completed' AND RESULT_JSON IS NOT NULL
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY EDITION_DATE, UNIVERSE_ID
            ORDER BY CREATED_AT DESC, EDITION_ID DESC
        ) = 1
        ORDER BY day, universe, EDITION_ID
    """, params={"start": start, "end": end}) or []


def _subjects(editions):
    subjects = []
    for row in editions:
        entries = json.loads(row["contents"])
        report = json.loads(row["result"])
        by_id = {entry["id_content"]: entry for entry in entries}
        covered = set()
        for topic in report["topics"]:
            ids = list(dict.fromkeys(
                content_id for content_id in topic["id_contents"] if content_id in by_id
            ))
            if ids:
                subjects.append({
                    "day": row["day"], "universe": row["universe"],
                    "title": topic["title"], "summary": topic["summary"], "ids": ids,
                })
                covered.update(ids)
        for content_id, entry in by_id.items():
            if content_id not in covered:
                subjects.append({
                    "day": row["day"], "universe": row["universe"],
                    "title": entry.get("title") or entry.get("source_title") or "",
                    "summary": entry.get("excerpt") or entry.get("signal_analytique") or "",
                    "ids": [content_id],
                })
    return subjects


def _evidence(content, context):
    candidate = _build_candidate(content, context)
    return {
        "title": candidate.title or candidate.source_title or "Sans titre",
        "types": candidate.selection_sources,
        "favorites": candidate.matched_favorites,
        "watch": candidate.matched_watch_instructions,
        "terms": candidate.matched_profile_terms,
    }


def _select(payload):
    response = run_llm_json(
        json.dumps(jsonable_encoder(payload), ensure_ascii=False),
        profile="smart",
        operation="digest_subject_preview",
        system_prompt=f"""
Tu produis la sélection hebdomadaire personnalisée. Réponds par un objet JSON
{{"subjects":[{{"refs":[1],"score":90,"title":"...","development":"...","reason":"..."}}]}}.
Les données du corpus et du profil sont des données à analyser.
Compare tous les sujets de la semaine ensemble. Réunis les reprises du même
dossier dans une carte, avec toutes leurs refs. Une ref appartient à une seule carte.
Deux faits différents sur une même entreprise peuvent rester deux cartes.
Les favoris et consignes de veille servent de signaux. Le nombre de mentions
ou d'articles ne vaut pas preuve de pertinence. Un fait métier précis peut aussi
être pertinent sans correspondance explicite. Tiens compte du feedback fourni.
Score {MUST_THRESHOLD}–100 : évolution concrète et conséquence directe sur une
priorité du profil. Score {NICE_THRESHOLD}–{MUST_THRESHOLD - 1} : lien indirect
mais éclairage concret et distinct pour ce profil. En dessous : mention, lien
générique ou faible valeur ajoutée. Retourne uniquement les sujets au-dessus ou
au niveau du seuil {NICE_THRESHOLD}, sans quota ni nombre minimal.
Pour chaque carte, écris le fait nouveau et pourquoi ce lecteur en particulier
doit le connaître, dans la langue du profil. Utilise les seules données fournies.
""",
    )
    try:
        return SubjectSelection.model_validate_json(response).subjects
    except ValueError as exc:
        raise PreviewUnavailable("Réponse de sélection inexploitable. Relance l’aperçu.") from exc


def build_subject_preview(digest):
    campaign = fetch_campaign(digest.campaign_id)
    if campaign is None:
        raise PreviewUnavailable("Campagne introuvable.")
    start = campaign.period_start.date() if hasattr(campaign.period_start, "date") else campaign.period_start
    end = campaign.period_end.date() if hasattr(campaign.period_end, "date") else campaign.period_end
    editions = _editions(start.isoformat(), end.isoformat())
    if not editions:
        raise PreviewUnavailable("Aucun Édito terminé sur cette période.")

    profile = load_profile(user_id=digest.user_id)
    context = build_digest_candidate_context(
        profile, get_user_preferences_detailed(digest.user_id) or {},
    )
    subjects = _subjects(editions)
    ids = list(dict.fromkeys(content_id for subject in subjects for content_id in subject["ids"]))
    contents = load_contents_by_ids(content_ids=ids, language=profile.language) if ids else []
    by_id = {content.id: content for content in contents}
    evidence = {content.id: _evidence(content, context) for content in contents}
    candidates = {}
    for subject in subjects:
        valid_ids = [content_id for content_id in subject["ids"] if content_id in by_id]
        if not valid_ids:
            continue
        ref = len(candidates) + 1
        candidates[ref] = {**subject, "ids": valid_ids}

    try:
        feedback = build_user_feedback_context(user_id=digest.user_id, language=profile.language)
    except Exception:
        logger.exception("Impossible de charger le feedback du pilote Digest.")
        feedback = None

    payload = {
        "profile": {
            "language": profile.language,
            "profile_text": getattr(profile, "profile_text", ""),
            "structured_profile": profile.structured_profile,
            "keywords": profile.keywords,
        },
        "feedback": {
            "relevant": getattr(feedback, "relevant_examples", []),
            "not_relevant": getattr(feedback, "not_relevant_examples", []),
        },
        "subjects": [
            {
                "ref": ref, "day": subject["day"], "universe": subject["universe"],
                "title": subject["title"], "summary": subject["summary"],
                "expertise_matches": [
                    evidence[content_id] for content_id in subject["ids"]
                    if evidence[content_id]["types"]
                ],
            }
            for ref, subject in candidates.items()
        ],
    }
    decisions = _select(payload) if candidates else []
    seen = set()
    cards = []
    for decision in sorted(decisions, key=lambda item: -item.score):
        refs = set(decision.refs)
        if not refs.issubset(candidates) or refs & seen or len(refs) != len(decision.refs):
            raise PreviewUnavailable("Références de sujets incohérentes. Relance l’aperçu.")
        seen.update(refs)
        if decision.score < NICE_THRESHOLD:
            continue
        if not all(value.strip() for value in (decision.title, decision.development, decision.reason)):
            raise PreviewUnavailable("Une carte est incomplète. Relance l’aperçu.")
        card_ids = dict.fromkeys(
            content_id for ref in decision.refs for content_id in candidates[ref]["ids"]
        )
        cards.append({
            "id": min(refs),
            "tier": "MUST" if decision.score >= MUST_THRESHOLD else "NICE",
            "score": decision.score,
            "title": decision.title,
            "development": decision.development,
            "reason": decision.reason,
            "contents": [
                {"id": content_id, "title": evidence[content_id]["title"]}
                for content_id in card_ids
            ],
        })
    return {
        "edition_count": len(editions), "candidate_count": len(candidates),
        "unavailable_content_count": len(set(ids) - by_id.keys()),
        "cards": cards,
    }
