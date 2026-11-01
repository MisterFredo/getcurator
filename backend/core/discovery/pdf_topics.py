"""PDF Studio V8 — document-wide editorial discovery with bounded evidence batches.

No persistence. No evidence is silently dropped. Local topic discovery is followed
by a global semantic merge; proposals remain subject to human review.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from typing import Any

from core.discovery.pdf_topics import propose_pdf_topics, _prepare_units
from utils.llm import run_llm_json

BATCH_UNITS = 100
MAX_MERGE_TOPICS = 180
MAX_MERGE_CHARS = 130_000
MAX_ATTEMPTS = 2

MERGE_PROMPT = """Tu consolides des PROPOSITIONS de sujets éditoriaux issues de plusieurs lots
DU MÊME document. Les lots sont artificiels : un sujet peut traverser les lots.
- Fusionne uniquement les sujets qui traitent réellement du même angle éditorial.
- Ne fusionne pas deux sujets simplement parce qu'ils partagent un pays, un mot ou un secteur.
- Ne supprime aucun sujet. Chaque ID doit apparaître UNE FOIS dans les groupes.
- Un sujet isolé doit être conservé comme groupe à un seul membre.
- Un titre et un angle factuels, autonomes, sans invention.
- N'ajoute aucune référence de preuve : les unit_ids seront réunis par le code.
Retourne UNIQUEMENT du JSON :
{"groups":[{"topic_ids":["B0001T0001"],"title":"Titre factuel","angle":"Angle précis","editorial_rationale":"Justification"}]}
"""


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _merge_topics(topics: list[dict[str, Any]], model: str | None) -> list[dict[str, Any]]:
    if len(topics) <= 1:
        return [{"topic_ids": [t["id"]], "title": t["title"],
                 "angle": t["angle"], "editorial_rationale": t["editorial_rationale"]} for t in topics]
    if len(topics) > MAX_MERGE_TOPICS:
        raise ValueError(
            f"{len(topics)} sujets provisoires : limite de consolidation globale "
            f"({MAX_MERGE_TOPICS}). Aucun sujet n'a été supprimé. "
            "Prévoir une consolidation hiérarchique avant de continuer."
        )
    cards = [{"id": t["id"], "title": t["title"], "angle": t["angle"],
              "editorial_rationale": t["editorial_rationale"],
              "evidence_count": len(t["unit_ids"])} for t in topics]
    prompt = json.dumps({"topics": cards}, ensure_ascii=False)
    if len(prompt) > MAX_MERGE_CHARS:
        raise ValueError("Sujets provisoires trop volumineux pour une consolidation globale fiable.")
    allowed = {t["id"] for t in topics}
    last_error: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            request = prompt if attempt == 0 else prompt + f"\nErreur précédente à corriger : {last_error}"
            raw = run_llm_json(
                prompt=request, model=model, temperature=0.0,
                system_prompt=MERGE_PROMPT, profile="smart",
                operation="pdf_studio_topic_global_merge",
            )
            parsed = json.loads(raw or "{}")
            groups = parsed.get("groups")
            if not isinstance(groups, list) or not groups:
                raise ValueError("groups absent ou vide")
            seen: set[str] = set()
            clean_groups = []
            for group in groups:
                if not isinstance(group, dict):
                    raise ValueError("Groupe invalide")
                ids = group.get("topic_ids")
                if not isinstance(ids, list) or not ids or any(not isinstance(v, str) for v in ids):
                    raise ValueError("topic_ids invalide")
                if len(set(ids)) != len(ids) or set(ids) - allowed or set(ids) & seen:
                    raise ValueError("IDs de sujets inconnus ou dupliqués")
                seen.update(ids)
                title = _clean(group.get("title"))
                angle = _clean(group.get("angle"))
                rationale = _clean(group.get("editorial_rationale"))
                if not title or not angle or not rationale:
                    raise ValueError("Métadonnées éditoriales incomplètes")
                clean_groups.append({"topic_ids": ids, "title": title, "angle": angle,
                                     "editorial_rationale": rationale})
            if seen != allowed:
                raise ValueError(f"{len(allowed - seen)} sujets provisoires manquants")
            return clean_groups
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            last_error = exc
    raise ValueError(f"Consolidation globale invalide : {last_error}")


def propose_pdf_topics_large(data: dict[str, Any], *, model: str | None = None) -> dict[str, Any]:
    """Process all eligible evidence; merge cross-batch topics with exact ID accounting.

    Input/output compatible with /pdf-studio/v8/topics. No automatic approval.
    """
    if not isinstance(data, dict):
        raise ValueError("Corpus documentaire JSON invalide.")
    # The existing validator assigns IDs to missing entries and separates rejected units.
    units, excluded = _prepare_all(data)
    by_id = {u["id"]: u for u in units}
    provisional: list[dict[str, Any]] = []
    for start in range(0, len(units), BATCH_UNITS):
        batch = units[start:start + BATCH_UNITS]
        local = propose_pdf_topics({
            "units": batch,
            "document_title": data.get("document_title"),
            "document_hash": data.get("document_hash"),
            "source_id": data.get("source_id"),
        }, model=model)
        batch_num = start // BATCH_UNITS + 1
        for proposal in local["proposals"]:
            provisional.append({
                "id": f"B{batch_num:04d}{proposal['id']}",
                "title": proposal["title"],
                "angle": proposal["angle"],
                "editorial_rationale": proposal["editorial_rationale"],
                "unit_ids": proposal["unit_ids"],
            })
    groups = _merge_topics(provisional, model)
    provisional_by_id = {t["id"]: t for t in provisional}
    covered: set[str] = set()
    proposals = []
    for index, group in enumerate(groups, 1):
        ids = list(dict.fromkeys(
            uid for tid in group["topic_ids"] for uid in provisional_by_id[tid]["unit_ids"]
        ))
        evidence = [by_id[uid] for uid in ids]
        covered.update(ids)
        review_count = sum(u["status"] != "VERIFIED" for u in evidence)
        proposals.append({
            "id": f"T{index:04d}", "title": group["title"], "angle": group["angle"],
            "editorial_rationale": group["editorial_rationale"],
            "unit_ids": ids, "pages": sorted({u["page"] for u in evidence}),
            "evidence_count": len(evidence),
            "exact_quote_count": len(evidence) - review_count,
            "review_count": review_count, "editorial_status": "REVIEW_REQUIRED",
            "evidence": evidence, "content_mode": "SOURCE_CONTENT",
            "merged_from": group["topic_ids"],
        })
    uncovered = [u for u in units if u["id"] not in covered]
    return {
        "status": "TOPICS_REVIEW_REQUIRED", "version": "8.0",
        "document_hash": data.get("document_hash"),
        "document_title": data.get("document_title"),
        "source_id": data.get("source_id"),
        "summary": {
            "input_units": len(data["units"]), "eligible_units": len(units),
            "excluded_units": len(excluded), "topic_proposals": len(proposals),
            "provisional_topics": len(provisional),
            "analysis_batches": (len(units) + BATCH_UNITS - 1) // BATCH_UNITS,
            "covered_units": len(covered), "uncovered_units": len(uncovered),
            "coverage_percent": round(100 * len(covered) / len(units), 1),
            "unit_statuses": dict(Counter(u["status"] for u in units)),
        },
        "proposals": proposals, "uncovered_evidence": uncovered,
        "excluded_evidence": excluded,
        "note": "Consolidation inter-lots ; aucun sujet approuvé automatiquement. VERIFIED atteste uniquement la correspondance textuelle de la citation.",
    }


def _prepare_all(data: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    raw = data.get("units")
    if not isinstance(raw, list):
        raise ValueError("Le champ units doit être une liste.")
    if not raw:
        raise ValueError("Aucune unité documentaire exploitable.")
    # Validate in slices to reuse existing status/quote normalization without its
    # 250-unit limit. Preserve global positional IDs and detect global duplicates.
    eligible: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    seen: set[str] = set()
    for start in range(0, len(raw), BATCH_UNITS):
        normalized = []
        for index, item in enumerate(raw[start:start + BATCH_UNITS], start + 1):
            if isinstance(item, dict):
                normalized.append({**item, "id": _clean(item.get("id")) or f"U{index:05d}"})
            else:
                normalized.append(item)
        # _prepare_units requires at least one eligible unit. Handle all-invalid slices
        # by using a known valid sentinel (removed after validation).
        sentinel = {"id": "__VALIDATION_SENTINEL__", "page": 1, "fact": "Validation sentinel", "status": "VERIFIED"}
        batch_eligible, batch_excluded = _prepare_units({"units": normalized + [sentinel]})
        batch_eligible = [u for u in batch_eligible if u["id"] != sentinel["id"]]
        for item in batch_eligible + batch_excluded:
            uid = item.get("id") or item.get("unit_id")
            if uid:
                if uid in seen:
                    raise ValueError(f"Identifiant d'unité dupliqué : {uid}")
                seen.add(uid)
        eligible.extend(batch_eligible)
        excluded.extend(batch_excluded)
    if not eligible:
        raise ValueError("Aucune unité documentaire exploitable.")
    return eligible, excluded
