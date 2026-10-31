"""PDF Studio V7 — one grounded synthesis per approved editorial unit.

No database writes. Source page numbers are 1-based.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any

from openai import OpenAI

MODEL = os.getenv("PDF_STUDIO_GENERATE_MODEL", os.getenv("PDF_STUDIO_MODEL", "gpt-4o-mini"))
MAX_SOURCE_CHARS = 90000
MAX_PAGES = 40
PAGE_REF = re.compile(r"\[p\.\s*(\d+)\]", re.I)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _pages(candidate: dict) -> list[dict]:
    source = candidate.get("pages")
    if not isinstance(source, list) or not source:
        raise ValueError("Le candidat ne contient aucune page source.")
    if len(source) > MAX_PAGES:
        raise ValueError(f"Maximum {MAX_PAGES} pages par article candidat.")
    result = []
    seen = set()
    for item in source:
        if not isinstance(item, dict):
            raise ValueError("Format de page invalide.")
        try:
            number = int(item.get("page"))
        except (TypeError, ValueError) as exc:
            raise ValueError("Numéro de page invalide.") from exc
        if number < 1 or number in seen:
            raise ValueError("Pages invalides ou dupliquées.")
        seen.add(number)
        text = _clean(item.get("text"))
        if text:
            result.append({"page": number, "text": text})
    if not result:
        raise ValueError("Aucun texte exploitable dans le candidat.")
    result.sort(key=lambda p: p["page"])
    if sum(len(p["text"]) for p in result) > MAX_SOURCE_CHARS:
        raise ValueError("Texte source trop volumineux pour une génération fiable.")
    return result


def _citations(text: str) -> set[int]:
    return {int(x) for x in PAGE_REF.findall(text or "")}


def _paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def generate_article(payload: dict) -> dict:
    """Generate one reviewable article from a V7 candidate; never import it."""
    if not isinstance(payload, dict):
        raise ValueError("Payload invalide.")
    candidate = payload.get("candidate")
    if not isinstance(candidate, dict):
        raise ValueError("Un candidat documentaire est obligatoire.")
    if _clean(candidate.get("review_status")) != "APPROVED":
        raise ValueError("Le candidat doit être approuvé avant génération.")
    if not _clean(candidate.get("title")):
        raise ValueError("Le titre du candidat est obligatoire.")
    document_title = _clean(payload.get("document_title"))
    source_id = _clean(payload.get("source_id"))
    if not document_title or not source_id:
        raise ValueError("Titre du document et identifiant source obligatoires.")

    pages = _pages(candidate)
    allowed = {p["page"] for p in pages}
    system = """Tu produis pour GetCurator UN article de synthèse en français par unité éditoriale du PDF.
La source fournie est la seule référence factuelle. Plusieurs thèmes dans la même unité
(par exemple un chapitre pays couvrant IA, paiements, logistique, réglementation) sont
NORMAUX : ne refuse pas l'article pour ce motif.

OBJECTIF : identifier les principaux enseignements, les faits et les chiffres vraiment
significatifs. Ne reproduis pas le document intégral et ne crée pas un article par rubrique.
Couvre les dimensions importantes, sans imposer une longueur artificielle (environ
300 à 700 mots si la matière le permet). Un titre informatif, un extrait court et
un corps structuré en paragraphes. Pas d'implications personnalisées : GetCurator
les calculera plus tard.

FIABILITÉ : aucune connaissance externe, aucun chiffre inventé, aucune extrapolation.
Respecte les réserves, les années, les prévisions et les attributions. Ne transforme
pas les données masquées de la version Light en chiffres. Ignore les en-têtes et
mentions répétées. Le texte PDF peut être désordonné (colonnes) : reconstitue le
sens prudemment; si un passage est ambigu, omets-le et signale-le en warnings.

TRAÇABILITÉ : chaque paragraphe factuel du body se termine par au moins une
référence de page exacte, par exemple [p. 33]. Chaque point clé porte une ou
plusieurs références de pages. Ne cite que les pages fournies.

Retourne UNIQUEMENT un objet JSON :
{
  "title": "...",
  "excerpt": "...",
  "body": "...",
  "key_points": ["Enseignement [p. 33]"],
  "warnings": [],
  "refusal_reason": null
}
Refuse uniquement si les pages sont inutilisables ou si aucun enseignement fiable
ne peut être extrait. Dans ce cas body="", key_points=[] et refusal_reason explique pourquoi.
"""
    request = {
        "document_title": document_title,
        "candidate": {
            "id": candidate.get("id"),
            "title": candidate.get("title"),
            "kind": candidate.get("kind"),
            "parent": candidate.get("parent"),
            "start_page": candidate.get("start_page"),
            "end_page": candidate.get("end_page"),
        },
        "source_pages": pages,
    }
    response = OpenAI(timeout=120, max_retries=2).chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(request, ensure_ascii=False)},
        ],
    )
    raw = response.choices[0].message.content or "{}"
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("Le modèle n'a pas retourné un JSON valide.") from exc
    if not isinstance(result, dict):
        raise ValueError("Réponse de génération invalide.")

    body = _clean(result.get("body"))
    excerpt = _clean(result.get("excerpt"))
    refusal = _clean(result.get("refusal_reason"))
    points = result.get("key_points")
    points = [_clean(p) for p in points if isinstance(p, str) and _clean(p)] if isinstance(points, list) else []
    raw_warnings = result.get("warnings")
    warnings = [_clean(w) for w in raw_warnings if isinstance(w, str) and _clean(w)] if isinstance(raw_warnings, list) else []

    cited = _citations(body + "\n" + "\n".join(points))
    invalid = sorted(cited - allowed)
    if invalid:
        warnings.append("Citations hors du candidat : " + ", ".join(map(str, invalid)))
    if body and not _citations(body):
        warnings.append("Le corps de l'article ne comporte aucune citation de page.")
    missing_paragraphs = [i for i, p in enumerate(_paragraphs(body), 1) if not _citations(p)]
    if body and missing_paragraphs:
        warnings.append("Paragraphes sans citation : " + ", ".join(map(str, missing_paragraphs)))
    missing_points = [i for i, p in enumerate(points, 1) if not _citations(p)]
    if points and missing_points:
        warnings.append("Points clés sans citation : " + ", ".join(map(str, missing_points)))

    valid = bool(body and not refusal and not invalid and not missing_paragraphs and not missing_points)
    if not valid:
        body = ""
        excerpt = ""
        points = []
        if not refusal:
            refusal = "Citations absentes ou invalides : régénération nécessaire."
    return {
        "status": "DRAFT_REVIEW_REQUIRED" if valid else "GENERATION_REJECTED",
        "version": "7.0",
        "proposal_id": candidate.get("id"),
        "document_hash": payload.get("document_hash"),
        "document_title": document_title,
        "source_id": source_id,
        "title": _clean(result.get("title")) or _clean(candidate.get("title")),
        "excerpt": excerpt,
        "body": body,
        "key_points": points,
        "cited_pages": sorted(cited) if valid else [],
        "warnings": warnings,
        "refusal_reason": refusal or None,
        "source_pages": pages,
        "model": MODEL,
    }
