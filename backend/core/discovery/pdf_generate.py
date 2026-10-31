"""PDF Studio V7.1 — one grounded factual dossier per approved editorial unit.

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
        raise ValueError(f"Maximum {MAX_PAGES} pages par fiche candidate.")
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
    """Generate one reviewable factual dossier from a V7 candidate; never import it."""
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
    system = """Tu prépares une FICHE DOCUMENTAIRE FACTUELLE en français destinée à alimenter
RATECARD_CONTENT_RAW puis le pipeline d'analyse GetCurator. Tu ne rédiges PAS un article.
Une unité documentaire cohérente = une fiche = un RAW. Plusieurs sujets dans une unité
(pays : marché, IA, paiements, réglementation, logistique...) doivent rester dans la
MÊME fiche, regroupés sous des rubriques thématiques.

MISSION : extraire et organiser la matière informationnelle utile présente dans les
pages fournies, sans la transformer en récit, sans introduction ou conclusion
rhétorique, sans transitions de remplissage et sans interprétation stratégique.
Cherche à préserver les faits substantiels, données chiffrées, comparaisons,
évolutions, acteurs, dates, conditions et réserves, plutôt qu'à limiter arbitrairement
le nombre de points. Évite les répétitions et les formulations vagues.

FORMAT DU CORPS (body) : texte brut structuré, immédiatement lisible et indexable.
Chaque rubrique commence par un intitulé sur une ligne (ex. « Marché et adoption »),
puis une ou plusieurs lignes « - Fait précis ... [p. N] ».
Une ligne peut couvrir un fait composite cohérent, mais pas plusieurs affirmations
sans rapport. Ne crée que les rubriques appuyées par les pages. Ne crée pas de rubrique
vide. La longueur suit la densité de la source : ni quota de mots ni quota de points.

CHIFFRES : conserver les valeurs significatives avec unité, population, géographie,
période et statut (observé, prévision, objectif) lorsque ces informations figurent dans
la source. Ne pas arrondir arbitrairement. Ne jamais compléter les données masquées,
absentes ou illisibles de la version Light. Si une statistique est ambiguë (par exemple
100 % d'acheteurs en ligne), ne pas la transformer en fait certain : conserver la
qualification source si elle est claire, sinon omettre et signaler en warnings.

FIDÉLITÉ : le texte source est la SEULE référence. Aucune connaissance extérieure,
aucune causalité ou conclusion inventée, aucune extrapolation, aucune recommandation
personnalisée. Distinguer les faits, déclarations attribuées et prévisions. Le texte
PDF peut être désordonné (colonnes, tableaux) : n'affirmer que ce qui est reconstitué
avec confiance. Signaler dans warnings les limites pertinentes et les pages
nécessitant une vérification visuelle si elles contiennent des données importantes.

TRAÇABILITÉ : CHAQUE ligne factuelle du body porte une ou plusieurs citations de page
exactes [p. 32]. Chaque élément de key_points est également cité. Ne citer que les
pages fournies. Les références servent à la vérification humaine ; elles ne prouvent
pas à elles seules la justesse de l'extraction.

CHAMPS : title = titre documentaire neutre et précis ; excerpt = description courte
factuelle de la portée de la fiche, sans conclusions nouvelles ; key_points =
quelques repères majeurs, facultatifs, non exhaustifs, qui ne remplacent pas le body.
Ne pas répéter tout le body dans key_points. Le body est la source principale de faits.

Retourne UNIQUEMENT un objet JSON :
{
  "title": "...",
  "excerpt": "...",
  "body": "Marché et adoption\n- Fait ... [p. 32]\n- Fait ... [p. 33]\n\nPaiements\n- Fait ... [p. 34]",
  "key_points": ["Repère majeur [p. 32]"],
  "warnings": [],
  "refusal_reason": null
}
Refuse seulement si les pages sont inutilisables ou si aucun fait fiable ne peut être
extrait. Dans ce cas body="", key_points=[] et refusal_reason explique pourquoi.
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
        warnings.append("La fiche ne comporte aucune citation de page.")
    factual_lines = [(i, line.strip()) for i, line in enumerate(body.splitlines(), 1)
                     if line.strip().startswith(("- ", "• ", "* "))]
    missing_paragraphs = [i for i, line in factual_lines if not _citations(line)]
    if body and not factual_lines:
        warnings.append("La fiche ne contient aucune ligne factuelle structurée.")
    if missing_paragraphs:
        warnings.append("Lignes factuelles sans citation : " + ", ".join(map(str, missing_paragraphs)))
    missing_points = [i for i, p in enumerate(points, 1) if not _citations(p)]
    if points and missing_points:
        warnings.append("Points clés sans citation : " + ", ".join(map(str, missing_points)))

    valid = bool(body and not refusal and not invalid and bool(factual_lines) and not missing_paragraphs and not missing_points)
    if not valid:
        body = ""
        excerpt = ""
        points = []
        if not refusal:
            refusal = "Fiche non structurée ou références absentes/invalides : régénération nécessaire."
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
