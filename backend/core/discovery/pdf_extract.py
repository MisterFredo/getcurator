"""PDF Studio: exhaustive evidence extraction with auditable validation.

Never discard a candidate silently. VERIFIED means the *quote* matches PDF text,
not that the model's interpretation is factually verified.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any

from openai import OpenAI
from core.discovery.pdf_studio import _load, _normalize

BATCH_SIZE = 5
MAX_PAGE_TEXT = 16000
KINDS = {"STATISTIC", "TREND", "COMPARISON", "STATEMENT", "PRACTICE", "REGULATION", "OTHER"}


def _canonical(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "").casefold()
    value = value.replace("\u00ad", "").replace("\u00a0", " ")
    value = re.sub(r"[\u2010-\u2015]", "-", value)
    return re.sub(r"\s+", " ", value).strip()


def _tokens(value: str) -> list[str]:
    return re.findall(r"\w+(?:[.,]\d+)*", _canonical(value), flags=re.UNICODE)


def _numbers(value: str) -> list[str]:
    # Compare literal numeric tokens; do not treat different numbers as a fuzzy match.
    return re.findall(r"(?<!\w)\d+(?:[.,]\d+)*(?:\s*%)?", _canonical(value))


def _verify_quote(quote: str, page_text: str) -> tuple[str, str, float]:
    if not quote:
        return "REJECTED", "MISSING_QUOTE", 0.0
    if len(quote) < 12:
        return "NEEDS_REVIEW", "SHORT_QUOTE", 0.0
    quote_c = _canonical(quote)
    page_c = _canonical(page_text)
    if quote_c in page_c:
        return "VERIFIED", "EXACT_TEXT_MATCH", 1.0
    qt, pt = _tokens(quote), _tokens(page_text)
    if not qt or not pt:
        return "NEEDS_REVIEW", "UNREADABLE_TEXT", 0.0
    # Search local windows rather than comparing a short quote to a full page.
    n = len(qt)
    best = 0.0
    for length in {max(1, n - 2), n, n + 2}:
        if length > len(pt):
            continue
        stride = 1 if len(pt) < 3500 else 2
        for i in range(0, len(pt) - length + 1, stride):
            window = pt[i:i + length]
            if _numbers(quote) and not set(_numbers(quote)).issubset(set(_numbers(" ".join(window)))):
                continue
            score = SequenceMatcher(None, qt, window, autojunk=False).ratio()
            best = max(best, score)
            if best >= 0.94:
                return "NEEDS_REVIEW", "NEAR_TEXT_MATCH", round(best, 3)
    return "NEEDS_REVIEW", "QUOTE_NOT_LOCATED", round(best, 3)


def extract_pdf_batch(pdf_bytes: bytes, start_page: int, *, model: str | None = None) -> dict[str, Any]:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY manquante")
    with _load(pdf_bytes) as doc:
        count = len(doc)
        if not 1 <= start_page <= count:
            raise ValueError("start_page hors des pages du document")
        end_page = min(count, start_page + BATCH_SIZE - 1)
        page_texts = {
            p: _normalize(doc[p - 1].get_text("text", sort=True))[:MAX_PAGE_TEXT]
            for p in range(start_page, end_page + 1)
        }

    source = "\n\n".join(f"=== PAGE PDF {p} ===\n{txt}" for p, txt in page_texts.items())
    client = OpenAI(timeout=100.0, max_retries=1)
    completion = client.chat.completions.create(
        model=model or os.getenv("PDF_STUDIO_MODEL", "gpt-4o-mini"),
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": (
                "Extrais de façon aussi exhaustive que possible les unités d'information distinctes. "
                "Ne sélectionne pas les meilleurs articles. N'invente rien. "
                "Une unité est un fait, chiffre avec unité/période, évolution, comparaison, "
                "déclaration attribuée, pratique ou règle explicitement décrite. "
                "Ignore en-têtes, sommaires, slogans et répétitions. Ne déduis pas de causalité. "
                "Retourne un objet JSON avec 'units' (liste). Chaque unité a 'page' (entier), "
                "'fact' (phrase autonome en français), 'quote' (citation originale courte, "
                "copiée littéralement), 'kind' (STATISTIC|TREND|COMPARISON|STATEMENT|PRACTICE|REGULATION|OTHER), "
                "'geography' (texte ou null), 'period' (texte ou null). "
                "Les pages correspondent aux délimiteurs PAGE PDF. "
                "Si un tableau est ambigu, signale seulement les faits clairement lisibles."
            )},
            {"role": "user", "content": source},
        ],
    )
    parsed = json.loads(completion.choices[0].message.content or "{}")
    raw_units = parsed.get("units", [])
    if not isinstance(raw_units, list):
        raise ValueError("Réponse IA invalide : units doit être une liste")

    results: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for index, unit in enumerate(raw_units):
        if not isinstance(unit, dict):
            results.append({"page": None, "fact": "", "quote": "", "kind": "OTHER",
                            "geography": None, "period": None, "status": "REJECTED",
                            "reason": "INVALID_ITEM", "match_score": 0.0, "needs_review": True,
                            "candidate_index": index})
            continue
        page = unit.get("page")
        fact = str(unit.get("fact") or "").strip()
        quote = str(unit.get("quote") or "").strip()
        kind = unit.get("kind") if unit.get("kind") in KINDS else "OTHER"
        result = {
            "page": page if type(page) is int else None,
            "fact": fact, "quote": quote, "kind": kind,
            "geography": unit.get("geography") if isinstance(unit.get("geography"), str) else None,
            "period": unit.get("period") if isinstance(unit.get("period"), str) else None,
            "needs_review": True, "candidate_index": index,
        }
        if type(page) is not int or page not in page_texts:
            status, reason, score = "REJECTED", "INVALID_PAGE", 0.0
        elif len(fact) < 15:
            status, reason, score = "REJECTED", "MISSING_OR_SHORT_FACT", 0.0
        else:
            status, reason, score = _verify_quote(quote, page_texts[page])
        key = (page, _canonical(fact), _canonical(quote))
        if key in seen:
            status, reason, score = "REJECTED", "DUPLICATE_IN_BATCH", 0.0
        seen.add(key)
        result.update(status=status, reason=reason, match_score=score)
        results.append(result)

    counts = {status: sum(u["status"] == status for u in results)
              for status in ("VERIFIED", "NEEDS_REVIEW", "REJECTED")}
    return {
        "status": "ok", "start_page": start_page, "end_page": end_page,
        "page_count": count, "next_page": end_page + 1 if end_page < count else None,
        "units": results, "counts": counts, "candidate_count": len(results),
        "rejected_unverified": counts["REJECTED"],
        "warning": "VERIFIED valide uniquement la correspondance textuelle de la citation. "
                   "Toutes les interprétations, statistiques et tableaux nécessitent encore une revue éditoriale.",
    }
