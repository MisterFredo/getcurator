
"""PDF Studio V6.3 — Generate a grounded draft from an approved document candidate.

No BigQuery writes.
The source of truth is the document segment, not consolidated evidence units.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from openai import OpenAI


MODEL = os.getenv(
    "PDF_STUDIO_GENERATE_MODEL",
    os.getenv("PDF_STUDIO_MODEL", "gpt-4o-mini"),
)

MAX_SOURCE_CHARS = 60000
MAX_PAGES = 30


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _normalize_pages(candidate: dict) -> list[dict]:
    """Normalize page text while preserving source page numbers."""

    pages = candidate.get("pages") or []

    if not isinstance(pages, list) or not pages:
        raise ValueError("Le candidat ne contient aucune page source.")

    if len(pages) > MAX_PAGES:
        raise ValueError(
            f"Maximum {MAX_PAGES} pages par candidat."
        )

    normalized = []
    seen = set()

    for item in pages:
        if not isinstance(item, dict):
            raise ValueError("Format de page invalide.")

        try:
            number = int(item.get("page"))
        except (TypeError, ValueError):
            raise ValueError("Numéro de page invalide.")

        if number < 1 or number in seen:
            raise ValueError("Pages invalides ou dupliquées.")

        text = _clean(item.get("text"))

        if text:
            normalized.append({
                "page": number,
                "text": text,
            })

        seen.add(number)

    if not normalized:
        raise ValueError("Aucun texte exploitable dans le candidat.")

    normalized.sort(key=lambda x: x["page"])

    return normalized


def _prepare_candidate(payload: dict) -> tuple[dict, list[dict]]:
    """Validate the candidate before sending any source text to the model."""

    candidate = payload.get("candidate")

    if not isinstance(candidate, dict):
        raise ValueError("Un candidat documentaire est obligatoire.")

    if _clean(candidate.get("review_status")) != "APPROVED":
        raise ValueError(
            "Le candidat doit être approuvé avant génération."
        )

    if candidate.get("generatable") is not True:
        raise ValueError(
            "Le candidat n'est pas validé comme contenu autonome."
        )

    if not _clean(payload.get("document_title")):
        raise ValueError("Le titre du document est obligatoire.")

    if not _clean(payload.get("source_id")):
        raise ValueError("L'identifiant de la source est obligatoire.")

    if not _clean(candidate.get("title")):
        raise ValueError("Le titre du candidat est obligatoire.")

    pages = _normalize_pages(candidate)

    total_chars = sum(len(p["text"]) for p in pages)

    if total_chars > MAX_SOURCE_CHARS:
        raise ValueError(
            "Segment trop long : découpage supplémentaire nécessaire."
        )

    return candidate, pages


def _extract_cited_pages(body: str) -> list[int]:
    """Extract explicit [p. N] references from the generated article."""

    values = re.findall(
        r"\[p\.\s*(\d+)\]",
        body or "",
        flags=re.IGNORECASE,
    )

    return sorted({int(value) for value in values})


def generate_article(payload: dict) -> dict:
    """Generate one editable article from an approved documentary segment."""

    candidate, pages = _prepare_candidate(payload)

    allowed_pages = {p["page"] for p in pages}

    instructions = """
Tu es un rédacteur B2B spécialisé dans l'analyse documentaire.

Tu produis un article autonome en français à partir d'un extrait
de document fourni par l'utilisateur.

Le texte source constitue ton unique référence factuelle.

OBJECTIF
Transformer un segment documentaire cohérent en article informatif,
fidèle au document original et directement exploitable dans GetCurator.

RÈGLES DE FIDÉLITÉ
- N'utilise aucune connaissance extérieure.
- N'invente aucun chiffre, aucune entreprise, aucune déclaration.
- Ne crée aucune relation causale absente du texte source.
- Préserve les nuances, réserves et limites des auteurs.
- Ne présente jamais une prévision comme un résultat observé.
- N'invente aucune donnée masquée ou absente de la version source.
- N'attribue pas à un pays une donnée concernant une autre zone.
- Ignore les en-têtes, pieds de page et mentions répétitives.

PÉRIMÈTRE
- Respecte le sujet et le périmètre du candidat.
- Ne fusionne pas artificiellement des sujets indépendants.
- Si le segment contient plusieurs sujets autonomes, refuse
  de produire un article unique et explique pourquoi.
- Ne complète pas un texte incomplet par des suppositions.

RÉDACTION
- Langue : français.
- Titre précis, informatif et non promotionnel.
- Extrait de deux phrases maximum.
- Corps structuré en paragraphes lisibles.
- Longueur indicative : 300 à 650 mots, uniquement si la
  matière documentaire est suffisante.
- Ne produis pas de remplissage pour atteindre cette longueur.
- Ne formule pas d'implications stratégiques personnalisées :
  elles relèvent de l'Expertise Engine de GetCurator.

CITATIONS
- Chaque paragraphe factuel doit contenir au moins une référence
  à la page source, au format exact [p. 32].
- Cite uniquement des pages présentes dans le segment.
- Ne prétends pas avoir vérifié des informations hors du document.

SORTIE
Retourne exclusivement un objet JSON valide avec :
{
  "title": "Titre",
  "excerpt": "Résumé court",
  "body": "Article avec références de pages",
  "warnings": [],
  "refusal_reason": null
}

Si le segment ne permet pas un article cohérent :
- body doit être une chaîne vide.
- refusal_reason doit expliquer le problème.
- warnings doit signaler les limites documentaires.
"""

    request_data = {
        "document_title": _clean(payload.get("document_title")),
        "candidate": {
            "id": candidate.get("id"),
            "title": candidate.get("title"),
            "kind": candidate.get("kind"),
            "country_primary": candidate.get("country_primary"),
            "region": candidate.get("region"),
            "start_page": candidate.get("start_page"),
            "end_page": candidate.get("end_page"),
        },
        "source_pages": pages,
    }

    response = OpenAI(
        timeout=120,
        max_retries=2,
    ).chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": instructions,
            },
            {
                "role": "user",
                "content": json.dumps(
                    request_data,
                    ensure_ascii=False,
                ),
            },
        ],
    )

    result = json.loads(
        response.choices[0].message.content or "{}"
    )

    if not isinstance(result, dict):
        raise ValueError("Réponse de génération invalide.")

    body = _clean(result.get("body"))
    refusal_reason = _clean(result.get("refusal_reason"))

    cited_pages = _extract_cited_pages(body)

    invalid_pages = [
        page for page in cited_pages
        if page not in allowed_pages
    ]

    warnings = result.get("warnings")

    if not isinstance(warnings, list):
        warnings = []

    warnings = [
        _clean(warning)
        for warning in warnings
        if _clean(warning)
    ]

    if invalid_pages:
        warnings.append(
            "Références à des pages absentes du segment : "
            + ", ".join(str(p) for p in invalid_pages)
        )
        body = ""

    if body and not cited_pages:
        warnings.append(
            "Article sans références de pages : validation impossible."
        )
        body = ""

    if refusal_reason:
        body = ""

    if not body and not refusal_reason:
        refusal_reason = (
            "Le segment ne permet pas de générer un article "
            "suffisamment cohérent ou correctement sourcé."
        )

    return {
        "status": (
            "DRAFT_REVIEW_REQUIRED"
            if body
            else "GENERATION_REJECTED"
        ),
        "version": "6.3",
        "proposal_id": candidate.get("id"),
        "document_hash": payload.get("document_hash"),
        "document_title": _clean(payload.get("document_title")),
        "source_id": _clean(payload.get("source_id")),
        "title": _clean(result.get("title")) or _clean(candidate.get("title")),
        "excerpt": _clean(result.get("excerpt")) if body else "",
        "body": body,
        "cited_pages": cited_pages if body else [],
        "warnings": warnings,
        "refusal_reason": refusal_reason or None,
        "source_pages": pages,
        "model": MODEL,
    }
