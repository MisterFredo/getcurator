"""PDF Studio V2 — exhaustive editorial grouping; no database writes.

Drop-in replacement for core/discovery/pdf_consolidate.py.
Keeps the V1 consolidate(data) API and response shape.
"""
from __future__ import annotations

import json
import os
import re
from collections import Counter, defaultdict
from typing import Any
from openai import OpenAI

MODEL = os.getenv("PDF_STUDIO_MODEL", "gpt-4o-mini")
BATCH_SIZE = 35


def ask(client: OpenAI, system: str, payload: dict[str, Any], model: str) -> dict[str, Any]:
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system + "\nRéponds uniquement par un objet JSON valide."},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
    )
    value = json.loads(response.choices[0].message.content or "{}")
    if not isinstance(value, dict):
        raise ValueError("Réponse JSON invalide du modèle")
    return value


def prepare(data: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for index, unit in enumerate(data.get("units", [])):
        if not isinstance(unit, dict) or unit.get("status") == "REJECTED" or not str(unit.get("fact") or "").strip():
            continue
        result.append({
            "id": f"U{index + 1:05d}",
            "page": unit.get("page"), "fact": unit["fact"],
            "quote": unit.get("quote", ""), "kind": unit.get("kind"),
            "geography": unit.get("geography"), "period": unit.get("period"),
            "status": unit.get("status", "NEEDS_REVIEW"),
            "reason": unit.get("reason"), "match_score": unit.get("match_score"),
        })
    return result


def _unique_ids(ids: Any, allowed: set[str]) -> list[str]:
    if not isinstance(ids, list):
        return []
    return list(dict.fromkeys(i for i in ids if isinstance(i, str) and i in allowed))


def _proposals(raw: Any, allowed: set[str]) -> list[dict[str, Any]]:
    output = []
    for p in raw if isinstance(raw, list) else []:
        if not isinstance(p, dict):
            continue
        title = str(p.get("title") or "").strip()
        ids = _unique_ids(p.get("unit_ids"), allowed)
        if title and len(ids) >= 2:
            output.append({
                "title": title,
                "angle": str(p.get("angle") or "").strip(),
                "scope": str(p.get("scope") or "").strip(),
                "editorial_rationale": str(p.get("editorial_rationale") or "").strip(),
                "unit_ids": ids,
            })
    return output


def _slug(value: str) -> str:
    return re.sub(r"\W+", " ", value.lower(), flags=re.UNICODE).strip()


def _dedupe(proposals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Only merge near-identical headings in the same scope; never discard their evidence."""
    merged: dict[tuple[str, str], dict[str, Any]] = {}
    for p in proposals:
        key = (_slug(p["title"]), _slug(p["scope"]))
        if key not in merged:
            merged[key] = {**p, "unit_ids": list(p["unit_ids"])}
        else:
            merged[key]["unit_ids"] = list(dict.fromkeys(merged[key]["unit_ids"] + p["unit_ids"]))
    return list(merged.values())


PROMPT = """Tu es rédacteur en chef B2B. Ton travail est de cartographier EXHAUSTIVEMENT les unités
sans rédiger d'articles. Propose autant de sujets éditoriaux spécifiques et distincts que justifiés.
Chaque sujet comporte un angle précis, un périmètre (pays ou transversal), et au moins 2 unit_ids.
Une unité peut soutenir plusieurs angles. Ne fusionne pas des pays/sujets sans justification.
NE PAS produire seulement une synthèse générale du lot. Cherche les sujets négligés (paiements,
logistique, réglementation, consommation, IA, durabilité, marchés, etc.).
Les unités dont la citation n'est pas vérifiée peuvent servir à la découverte de sujets, mais
aucune information n'est considérée validée pour publication.
Rends {"proposals":[{"title":"...","angle":"...","scope":"...",
"editorial_rationale":"...","unit_ids":["U00001","U00002"]}],
"singletons":[{"unit_id":"U00003","reason":"..."}]}.
Toute unité doit être soit utilisée dans au moins une proposition, soit mentionnée dans singletons.
Ne cite que des IDs fournis. N'invente aucun fait."""


def _batch(client: OpenAI, batch: list[dict[str, Any]], model: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    allowed = {u["id"] for u in batch}
    payload = {"units": [{k: u.get(k) for k in ("id", "page", "fact", "kind", "geography", "period", "status")} for u in batch]}
    result = ask(client, PROMPT, payload, model)
    proposals = _proposals(result.get("proposals"), allowed)
    singletons = [s for s in result.get("singletons", []) if isinstance(s, dict) and s.get("unit_id") in allowed] if isinstance(result.get("singletons"), list) else []
    return proposals, singletons


def consolidate(data: dict[str, Any], model: str = MODEL) -> dict[str, Any]:
    units = prepare(data)
    if not units:
        raise ValueError("Aucune unité exploitable dans l'extraction")
    by_id = {u["id"]: u for u in units}
    client = OpenAI(timeout=120, max_retries=2)
    proposals: list[dict[str, Any]] = []
    singletons: list[dict[str, Any]] = []
    # Stage 1: all units are presented to the model, in bounded batches.
    for offset in range(0, len(units), BATCH_SIZE):
        p, s = _batch(client, units[offset:offset + BATCH_SIZE], model)
        proposals.extend(p)
        singletons.extend(s)
    local_count = len(proposals)

    # Stage 2: recovery of unused evidence, WITHOUT allowing a global LLM pass
    # to reduce the final list to ten broad subjects.
    used = {i for p in proposals for i in p["unit_ids"]}
    missing = [u for u in units if u["id"] not in used]
    recovery_count = 0
    for offset in range(0, len(missing), BATCH_SIZE):
        p, s = _batch(client, missing[offset:offset + BATCH_SIZE], model)
        proposals.extend(p)
        singletons.extend(s)
        recovery_count += len(p)

    # Stage 3: conservative exact-title deduplication. Broad semantic merges
    # would recreate the coverage collapse seen in V1.
    proposals = _dedupe(proposals)
    final: list[dict[str, Any]] = []
    used = set()
    for index, p in enumerate(proposals, 1):
        evidence = [by_id[i] for i in p["unit_ids"]]
        used.update(p["unit_ids"])
        final.append({
            **p, "id": f"A{index:04d}",
            "pages": sorted({u["page"] for u in evidence if isinstance(u["page"], int)}),
            "evidence_count": len(evidence),
            "exact_quote_count": sum(u["status"] == "VERIFIED" for u in evidence),
            "review_count": sum(u["status"] != "VERIFIED" for u in evidence),
            "editorial_status": "REVIEW_REQUIRED", "evidence": evidence,
        })
    # A standalone fact is preserved, not forced into an artificial article.
    uncovered = [u for u in units if u["id"] not in used]
    return {
        "document_hash": data.get("document_hash"),
        "document_title": data.get("document_title"),
        "source_id": data.get("source_id"), "model": model,
        "version": "2.0",
        "summary": {
            "input_units": len(units), "local_proposals": local_count,
            "recovery_proposals": recovery_count,
            "article_proposals": len(final),
            "covered_units": len(used), "uncovered_units": len(uncovered),
            "coverage_percent": round(100 * len(used) / len(units), 1),
            "unit_statuses": dict(Counter(u["status"] for u in units)),
        },
        "proposals": final,
        "uncovered_evidence": uncovered,
        "singletons": singletons,
        "note": "Editorial candidates only. No generated articles or DB writes. Review source claims and numbers before publication.",
    }
