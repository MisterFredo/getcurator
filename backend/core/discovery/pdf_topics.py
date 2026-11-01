"""PDF Studio V8 — evidence-grounded editorial topic discovery.

Input: accumulated, reviewed or unreviewed units from PDF extraction.
Output: auditable editorial topic proposals; no articles and no database writes.

Every eligible evidence unit is either linked to at least one proposed topic or
explicitly listed as uncovered. VERIFIED certifies a quote match, not its meaning.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from typing import Any

from utils.llm import run_llm_json

MAX_UNITS = 250
MAX_PROMPT_CHARS = 150_000
MAX_ATTEMPTS = 2

SYSTEM_PROMPT = """Tu es responsable de l'identification des sujets éditoriaux d'un document PDF.
Tu reçois des unités documentaires extraites, avec leurs identifiants et pages.

MISSION : identifier les sujets RÉELLEMENT étayés par les unités, pas découper
artificiellement le PDF, ni le résumer globalement.

RÈGLES :
- Propose autant de sujets distincts que le corpus le justifie, sans quota.
- Un sujet = une question ou un fait central autonome, intelligible hors du PDF.
- Plusieurs unités d'un même sujet peuvent provenir de pages éloignées.
- Une unité peut soutenir plusieurs sujets, uniquement si c'est pertinent.
- Ne regroupe pas des unités au seul motif qu'elles partagent une géographie,
  une période, un mot-clé ou des pages voisines.
- Ne sépare pas artificiellement un même sujet en plusieurs propositions.
- Une seule unité substantielle peut justifier un sujet.
- Ne fabrique aucun chiffre, aucune causalité, aucun acteur, aucun contexte.
- Les unités NEEDS_REVIEW sont utilisables mais doivent être signalées comme
  nécessitant une vérification humaine ; VERIFIED n'atteste que la citation.
- Les unités trop isolées ou insuffisantes peuvent rester non attribuées.
- Pour chaque sujet, cite UNIQUEMENT les IDs d'unités fournis.
- Donne un titre factuel, un angle précis, et une justification de la cohérence.
- N'écris PAS les articles et ne décide PAS de leur approbation.

Retourne uniquement un objet JSON :
{
  "topics": [
    {
      "title": "Titre factuel autonome",
      "angle": "Sujet précis et périmètre du futur contenu",
      "editorial_rationale": "Pourquoi ces faits constituent un sujet cohérent",
      "unit_ids": ["U00001"]
    }
  ]
}
"""


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _prepare_units(data: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    raw_units = data.get("units")
    if not isinstance(raw_units, list):
        raise ValueError("Le champ units doit être une liste.")

    eligible: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    ids: set[str] = set()

    for index, raw in enumerate(raw_units, 1):
        if not isinstance(raw, dict):
            excluded.append({"input_index": index, "reason": "INVALID_ITEM"})
            continue

        unit_id = _clean(raw.get("id")) or f"U{index:05d}"
        if unit_id in ids:
            raise ValueError(f"Identifiant d'unité dupliqué : {unit_id}")
        ids.add(unit_id)

        status = _clean(raw.get("status") or "NEEDS_REVIEW").upper()
        fact = _clean(raw.get("fact"))
        page = raw.get("page")
        if status == "REJECTED" or not fact or type(page) is not int or page < 1:
            excluded.append({
                "unit_id": unit_id,
                "page": page,
                "reason": "REJECTED" if status == "REJECTED" else "INVALID_EVIDENCE",
            })
            continue
        if status not in {"VERIFIED", "NEEDS_REVIEW"}:
            raise ValueError(f"Statut d'unité inconnu : {unit_id} ({status})")

        eligible.append({
            "id": unit_id,
            "page": page,
            "fact": fact,
            "kind": _clean(raw.get("kind")) or "OTHER",
            "geography": _clean(raw.get("geography")) or None,
            "period": _clean(raw.get("period")) or None,
            "status": status,
            "quote": _clean(raw.get("quote")),
        })

    if not eligible:
        raise ValueError("Aucune unité documentaire exploitable.")
    if len(eligible) > MAX_UNITS:
        raise ValueError(
            f"{len(eligible)} unités exploitables : limite de {MAX_UNITS} par analyse. "
            "Traiter le document en plusieurs corpus, puis consolider les sujets."
        )
    return eligible, excluded


def _validate_topics(parsed: Any, units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(parsed, dict) or not isinstance(parsed.get("topics"), list):
        raise ValueError("Réponse invalide : topics doit être une liste.")

    allowed = {unit["id"] for unit in units}
    topics: list[dict[str, Any]] = []
    signatures: set[frozenset[str]] = set()

    for index, raw in enumerate(parsed["topics"], 1):
        if not isinstance(raw, dict):
            raise ValueError(f"Sujet {index} invalide.")
        title = _clean(raw.get("title"))
        angle = _clean(raw.get("angle"))
        rationale = _clean(raw.get("editorial_rationale"))
        ids = raw.get("unit_ids")
        if not title or not angle or not rationale:
            raise ValueError(f"Sujet {index} : titre, angle ou justification absent.")
        if not isinstance(ids, list) or not ids or any(not isinstance(v, str) for v in ids):
            raise ValueError(f"Sujet {index} : liste unit_ids invalide.")
        if len(ids) != len(set(ids)):
            raise ValueError(f"Sujet {index} : unités répétées.")
        unknown = set(ids) - allowed
        if unknown:
            raise ValueError(f"Sujet {index} : unités inconnues {sorted(unknown)}.")
        signature = frozenset(ids)
        if signature in signatures:
            raise ValueError(f"Sujet {index} : même ensemble de preuves qu'un autre sujet.")
        signatures.add(signature)
        topics.append({
            "id": f"T{index:04d}",
            "title": title,
            "angle": angle,
            "editorial_rationale": rationale,
            "unit_ids": ids,
        })
    return topics


def propose_pdf_topics(
    data: dict[str, Any],
    *,
    model: str | None = None,
) -> dict[str, Any]:
    """Discover editorial topics from accumulated evidence units.

    Expects {units: [{id?, page, fact, status, ...}], document_hash?,
    document_title?, source_id?}. No persistence or article generation.
    """
    if not isinstance(data, dict):
        raise ValueError("Corpus documentaire JSON invalide.")

    units, excluded = _prepare_units(data)
    unit_by_id = {unit["id"]: unit for unit in units}
    prompt_data = {
        "document_title": _clean(data.get("document_title")),
        "units": units,
    }
    prompt = json.dumps(prompt_data, ensure_ascii=False)
    if len(prompt) > MAX_PROMPT_CHARS:
        raise ValueError(
            "Corpus trop volumineux pour une analyse éditoriale unique. "
            "Fractionner explicitement le corpus sans supprimer d'unités."
        )

    last_error: Exception | None = None
    topics: list[dict[str, Any]] | None = None
    for attempt in range(MAX_ATTEMPTS):
        request = prompt
        if attempt and last_error is not None:
            request += (
                "\n\nLa réponse précédente était invalide. "
                f"Corrige uniquement ce problème : {last_error}"
            )
        try:
            raw = run_llm_json(
                prompt=request,
                model=model,
                temperature=0.0,
                system_prompt=SYSTEM_PROMPT,
                profile="smart",
                operation="pdf_studio_topic_discovery",
            )
            topics = _validate_topics(json.loads(raw or "{}"), units)
            break
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            last_error = exc

    if topics is None:
        raise ValueError(f"Identification éditoriale invalide après {MAX_ATTEMPTS} essais : {last_error}")

    covered: set[str] = set()
    proposals: list[dict[str, Any]] = []
    for topic in topics:
        evidence = [unit_by_id[unit_id] for unit_id in topic["unit_ids"]]
        covered.update(topic["unit_ids"])
        pages = sorted({unit["page"] for unit in evidence})
        review_count = sum(unit["status"] != "VERIFIED" for unit in evidence)
        proposals.append({
            **topic,
            "pages": pages,
            "evidence_count": len(evidence),
            "exact_quote_count": len(evidence) - review_count,
            "review_count": review_count,
            "editorial_status": "REVIEW_REQUIRED",
            "evidence": evidence,
            "content_mode": "SOURCE_CONTENT",
        })

    uncovered = [unit for unit in units if unit["id"] not in covered]
    return {
        "status": "TOPICS_REVIEW_REQUIRED",
        "version": "8.0",
        "document_hash": data.get("document_hash"),
        "document_title": data.get("document_title"),
        "source_id": data.get("source_id"),
        "summary": {
            "input_units": len(data["units"]),
            "eligible_units": len(units),
            "excluded_units": len(excluded),
            "topic_proposals": len(proposals),
            "covered_units": len(covered),
            "uncovered_units": len(uncovered),
            "coverage_percent": round(100 * len(covered) / len(units), 1),
            "unit_statuses": dict(Counter(unit["status"] for unit in units)),
        },
        "proposals": proposals,
        "uncovered_evidence": uncovered,
        "excluded_evidence": excluded,
        "note": (
            "Sujets proposés à partir des unités documentaires. "
            "Aucun sujet n'est approuvé automatiquement ; les citations VERIFIED "
            "n'attestent pas la validité de l'interprétation."
        ),
    }
