"""PDF Studio — extraction of evidence units, in bounded page batches.

No database writes. The caller must retain the results until persistence is built.
The model must provide exact quotes; unmatched quotes are rejected.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any

from openai import OpenAI
from core.discovery.pdf_studio import _load, _normalize

BATCH_SIZE = 5
MAX_PAGE_TEXT = 16000


def _canonical(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").replace("\u00a0", " ")).strip().casefold()


def extract_pdf_batch(pdf_bytes: bytes, start_page: int, *, model: str | None = None) -> dict[str, Any]:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY manquante")
    with _load(pdf_bytes) as doc:
        count = len(doc)
        if not 1 <= start_page <= count:
            raise ValueError("start_page hors des pages du document")
        end_page = min(count, start_page + BATCH_SIZE - 1)
        page_texts = {}
        for p in range(start_page, end_page + 1):
            page_texts[p] = _normalize(doc[p - 1].get_text("text", sort=True))[:MAX_PAGE_TEXT]

    source = "\n\n".join(f"=== PAGE PDF {p} ===\n{txt}" for p, txt in page_texts.items())
    client = OpenAI(timeout=100.0, max_retries=1)
    completion = client.chat.completions.create(
        model=model or os.getenv("PDF_STUDIO_MODEL", "gpt-4o-mini"),
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": (
                "Tu extrais de façon exhaustive les unités d'information distinctes d'un document. "
                "Ne sélectionne pas les meilleures idées d'articles et n'invente rien. "
                "Une unité est un fait, un chiffre avec unité/période, une évolution, une comparaison, "
                "une déclaration attribuée, une pratique ou une règle explicitement décrite. "
                "Ignore les en-têtes, pieds de page, sommaires, slogans et répétitions. "
                "Ne déduis pas de causalité non exprimée. "
                "Retourne uniquement un objet JSON avec la clé 'units' contenant une liste. "
                "Chaque unité: 'page' (entier), 'fact' (phrase autonome en français), "
                "'quote' (citation exacte courte en langue originale copiée du texte fourni), "
                "'kind' (STATISTIC|TREND|COMPARISON|STATEMENT|PRACTICE|REGULATION|OTHER), "
                "'geography' (chaîne ou null), 'period' (chaîne ou null). "
                "Les numéros de page doivent correspondre aux délimiteurs PAGE PDF. "
                "Si un tableau est ambigu ou une donnée incomplète, ne la transforme pas en affirmation."
            )},
            {"role": "user", "content": source},
        ],
    )
    parsed = json.loads(completion.choices[0].message.content or "{}")
    units = parsed.get("units", [])
    if not isinstance(units, list):
        raise ValueError("Réponse IA invalide : units doit être une liste")
    accepted = []
    rejected = 0
    seen = set()
    kinds = {"STATISTIC", "TREND", "COMPARISON", "STATEMENT", "PRACTICE", "REGULATION", "OTHER"}
    for unit in units:
        if not isinstance(unit, dict):
            rejected += 1
            continue
        page = unit.get("page")
        quote = str(unit.get("quote") or "").strip()
        fact = str(unit.get("fact") or "").strip()
        if (type(page) is not int or page not in page_texts or len(quote) < 12 or
                len(fact) < 15 or _canonical(quote) not in _canonical(page_texts[page])):
            rejected += 1
            continue
        key = (page, _canonical(quote))
        if key in seen:
            continue
        seen.add(key)
        accepted.append({
            "page": page,
            "fact": fact,
            "quote": quote,
            "kind": unit.get("kind") if unit.get("kind") in kinds else "OTHER",
            "geography": unit.get("geography") if isinstance(unit.get("geography"), str) else None,
            "period": unit.get("period") if isinstance(unit.get("period"), str) else None,
            "needs_review": True,
        })
    return {
        "status": "ok", "start_page": start_page, "end_page": end_page,
        "page_count": count, "next_page": end_page + 1 if end_page < count else None,
        "units": accepted, "rejected_unverified": rejected,
        "warning": "Citations vérifiées dans le texte extrait, mais chiffres/tableaux et interprétations restent à contrôler visuellement.",
    }
