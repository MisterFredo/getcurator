"""PDF Studio V7.2 — exhaustive page-by-page factual dossier per approved editorial unit.

No database writes. Source page numbers are 1-based.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any

from utils.llm import run_llm_json

MODEL = os.getenv("PDF_STUDIO_GENERATE_MODEL") or os.getenv("PDF_STUDIO_MODEL") or None
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


def _model_json(system: str, data: dict) -> dict:
    raw_content = run_llm_json(
        prompt=json.dumps(data, ensure_ascii=False),
        model=MODEL,
        temperature=0.0,
        system_prompt=system,
        profile="smart",
        operation="pdf_studio_page_facts",
    )
    try:
        result = json.loads(raw_content or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError("Réponse JSON du modèle invalide.") from exc
    if not isinstance(result, dict):
        raise ValueError("Réponse du modèle non structurée.")
    return result


EXTRACTION_PROMPT = """Tu es un extracteur documentaire, PAS un rédacteur ni un synthétiseur.
Tu travailles EXCLUSIVEMENT sur le texte d'UNE page de PDF fournie.

OBJECTIF : EXTRACTION AUSSI EXHAUSTIVE QUE POSSIBLE DES INFORMATIONS SIGNIFICATIVES.
- Recense TOUTES les affirmations substantielles distinctes : chiffres, valeurs,
  dates, évolutions, comparaisons, entreprises, produits, politiques, contraintes,
  comportements, technologies, prévisions, déclarations et réserves.
- Ne privilégie PAS certains thèmes. Ne filtre PAS par intérêt présumé du lecteur.
- Un bullet = une information autonome. Si une phrase comporte trois informations
  distinctes, crée trois bullets. Garde le contexte nécessaire à leur compréhension.
- Reprends les valeurs, unités, années, populations, géographies et nuances exactes.
- Ne transforme jamais un chiffre ambigu en certitude. Signale-le en warnings.
- N'invente aucun fait ni donnée absente, masquée ou illisible.
- Évite seulement les doublons, les éléments décoratifs et les phrases sans contenu.
- Pour un tableau correctement lisible, préserve chaque valeur informative et
  les libellés associés. Si l'ordre du texte rend le tableau illisible, avertis.
- N'invente ni interprétation ni conséquence stratégique.
- Chaque bullet se termine par la référence exacte [p. N] fournie.
- Chaque page est traitée indépendamment afin d'éviter les omissions causées par
  un résumé global. Une page intercalaire peut avoir zéro bullet.

Retourne UNIQUEMENT un JSON :
{
 "sections": [
   {"heading": "Nom du thème", "bullets": ["Fait précis [p. N]"]}
 ],
 "warnings": []
}
Ne limite jamais arbitrairement le nombre de bullets ou de sections.
"""


def _page_facts(page: dict, document_title: str, candidate_title: str) -> tuple[list[tuple[str, str]], list[str]]:
    number = page["page"]
    result = _model_json(EXTRACTION_PROMPT, {
        "document_title": document_title,
        "unit_title": candidate_title,
        "page": number,
        "text": page["text"],
    })
    sections = result.get("sections")
    if not isinstance(sections, list):
        raise ValueError(f"Page {number} : sections absentes de la réponse.")
    facts: list[tuple[str, str]] = []
    for section in sections:
        if not isinstance(section, dict):
            raise ValueError(f"Page {number} : rubrique invalide.")
        heading = _clean(section.get("heading")) or "Informations générales"
        bullets = section.get("bullets")
        if not isinstance(bullets, list):
            raise ValueError(f"Page {number} : liste de faits invalide.")
        for bullet in bullets:
            line = _clean(bullet)
            if not line:
                continue
            citations = _citations(line)
            if citations != {number}:
                raise ValueError(f"Page {number} : citation manquante ou incorrecte : {line[:120]}")
            if line.startswith(("- ", "* ", "• ")):
                line = line[2:].strip()
            facts.append((heading, line))
    warnings = result.get("warnings")
    warnings = [_clean(w) for w in warnings if _clean(w)] if isinstance(warnings, list) else []
    return facts, [f"p. {number} : {w}" for w in warnings]


def generate_article(payload: dict) -> dict:
    """V7.2: page-wise exhaustive bullet extraction, one dossier per unit, one RAW."""
    if not isinstance(payload, dict):
        raise ValueError("Payload invalide.")
    candidate = payload.get("candidate")
    if not isinstance(candidate, dict) or _clean(candidate.get("review_status")) != "APPROVED":
        raise ValueError("Un candidat approuvé est obligatoire.")
    candidate_title = _clean(candidate.get("title"))
    document_title = _clean(payload.get("document_title"))
    source_id = _clean(payload.get("source_id"))
    if not candidate_title or not document_title or not source_id:
        raise ValueError("Titre du candidat, titre du document et source obligatoires.")
    pages = _pages(candidate)
    allowed = {p["page"] for p in pages}
    warnings: list[str] = []
    groups: dict[str, list[str]] = {}
    seen: set[str] = set()
    page_counts: dict[int, int] = {}

    # A separate model call per page prevents global summary compression.
    # Preserve all distinct facts; do not ask a second LLM to shorten the result.
    for page in pages:
        facts, page_warnings = _page_facts(page, document_title, candidate_title)
        warnings.extend(page_warnings)
        page_counts[page["page"]] = len(facts)
        if not facts:
            warnings.append(f"p. {page['page']} : aucun fait extrait ; vérifier la page dans le PDF.")
        for heading, line in facts:
            # Only deduplicate exact repeated wording, never approximate similarities.
            key = re.sub(r"\s+", " ", line).casefold()
            if key in seen:
                continue
            seen.add(key)
            groups.setdefault(heading, []).append(line)

    body = "\n\n".join(
        heading + "\n" + "\n".join("- " + bullet for bullet in bullets)
        for heading, bullets in groups.items() if bullets
    )
    citations = _citations(body)
    invalid = citations - allowed
    if invalid:
        raise ValueError("Citations hors du périmètre du candidat.")
    factual_lines = [line for line in body.splitlines() if line.startswith("- ")]
    if any(not _citations(line) for line in factual_lines):
        raise ValueError("Au moins un fait ne possède pas de citation.")
    valid = bool(factual_lines)
    return {
        "status": "DRAFT_REVIEW_REQUIRED" if valid else "GENERATION_REJECTED",
        "version": "7.0",  # Keep the existing V7 API/import contract.
        "proposal_id": candidate.get("id"),
        "document_hash": payload.get("document_hash"),
        "document_title": document_title,
        "source_id": source_id,
        "title": candidate_title,
        "excerpt": (f"Extraction documentaire factuelle de {candidate_title}, "
                    f"issue de {document_title}, pages {pages[0]['page']} à {pages[-1]['page']}."),
        "body": body,
        "key_points": [],  # No editorial highlights: all facts belong in the body.
        "cited_pages": sorted(citations),
        "warnings": warnings,
        "refusal_reason": None if valid else "Aucun fait fiable extrait des pages fournies.",
        "source_pages": pages,
        "model": MODEL or os.getenv("OPENAI_MODEL_SMART") or os.getenv("OPENAI_MODEL_DEFAULT"),
        "page_fact_counts": page_counts,
    }
