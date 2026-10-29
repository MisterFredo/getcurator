"""PDF Studio V5 — acquisition-first, drop-in consolidate(data) implementation.

One meaningful evidence unit is enough for a candidate RAW content. Related units
may be combined, but never at the cost of leaving most evidence unprocessed.
No external API calls, no database writes. Human verification is still required.
"""
from __future__ import annotations

import os
import re
import unicodedata
from collections import Counter, defaultdict
from typing import Any

MODEL = os.getenv("PDF_STUDIO_MODEL", "gpt-4o-mini")
MAX_PER_CONTENT = max(1, int(os.getenv("PDF_STUDIO_V5_MAX_UNITS_PER_CONTENT", "3")))
MAX_PAGE_GAP = max(0, int(os.getenv("PDF_STUDIO_V5_MAX_PAGE_GAP", "1")))

THEME_RULES = [
    ("PAYMENTS", r"paiement|payment|bnpl|bancontact|ideal|twint|swish|carte bancaire|credit card|transaction"),
    ("LOGISTICS", r"livraison|delivery|colis|parcel|logist|last.mile|dernier kilom|locker|consigne|transporteur|shipping|inpost|postnord|dhl|dpd"),
    ("AI_TECH", r"\bia\b|\bai\b|artificial intelligence|intelligence artificielle|agentic|automatis|technolog"),
    ("REGULATION", r"réglement|regulat|douan|customs|tarif|compliance|conformit|directive|législat|legislat"),
    ("SUSTAINABILITY", r"durab|sustainab|circulair|circular|recycl|environ|seconde main|second.hand|refurbish"),
    ("CROSS_BORDER", r"transfrontal|cross.border|import|export|pays tiers|third.country"),
    ("MARKETPLACES", r"marketplace|plateforme|platform|amazon|temu|shein|google|moteur de recherche|search engine"),
    ("BUSINESS_DIGITALIZATION", r"entrepris|enterprise|pme|sme|digitalis|numéri|numériq|ict|tic|formation|skills"),
    ("CONSUMER_BEHAVIOR", r"consommateur|consumer|acheteur|shopper|achats en ligne|online purchas|sensib|comportement|panier|basket"),
    ("MARKET_GROWTH", r"chiffre d.affaires|turnover|croissance|growth|\bpib\b|\bgdp\b|marché|market|e.commerce|commerce électronique|vente"),
]

ALIASES = {
    "belgium":"Belgique", "ireland":"Irlande", "united kingdom":"Royaume-Uni",
    "uk":"Royaume-Uni", "germany":"Allemagne", "netherlands":"Pays-Bas",
    "denmark":"Danemark", "sweden":"Suède", "norway":"Norvège",
    "poland":"Pologne", "finland":"Finlande", "austria":"Autriche",
    "spain":"Espagne", "italy":"Italie", "romania":"Roumanie",
    "switzerland":"Suisse", "bosnia herzegovina":"Bosnie-Herzégovine",
    "bosnia and herzegovina":"Bosnie-Herzégovine", "croatia":"Croatie",
    "albania":"Albanie", "hungary":"Hongrie", "slovenia":"Slovénie",
    "slovak republic":"Slovaquie", "serbia":"Serbie", "moldova":"Moldavie",
    "montenegro":"Monténégro", "north macedonia":"Macédoine du Nord",
    "malta":"Malte", "eu":"UE-27", "eu 27":"UE-27",
    "union europeenne":"UE-27", "european union":"UE-27",
    "southern europe":"Europe du Sud", "northern europe":"Europe du Nord",
    "eastern europe":"Europe de l'Est", "western europe":"Europe de l'Ouest",
}

def _norm(value: Any) -> str:
    v = unicodedata.normalize("NFKD", str(value or "").lower())
    return re.sub(r"[^a-z0-9]+", " ", "".join(c for c in v if not unicodedata.combining(c))).strip()

def _scope(value: Any) -> str:
    raw = str(value or "Non précisé").strip()
    return ALIASES.get(_norm(raw), raw)

def _theme(fact: str, kind: Any) -> str:
    s = _norm(fact)
    for name, pattern in THEME_RULES:
        if re.search(pattern, s):
            return name
    if str(kind).upper() == "REGULATION":
        return "REGULATION"
    return "OTHER"

def _title(fact: str, scope: str) -> str:
    # Do not invent an angle: title is an excerpt of the actual extracted fact.
    fact = re.sub(r"\s+", " ", str(fact or "")).strip().rstrip(". ;:")
    if len(fact) > 155:
        fact = fact[:152].rsplit(" ", 1)[0].rstrip(",;:") + "…"
    return fact[:1].upper() + fact[1:] if fact else f"Information sur {scope}"

def _page(u: dict) -> int | None:
    p = u.get("page")
    return p if isinstance(p, int) and not isinstance(p, bool) and p > 0 else None

def consolidate(data: dict[str, Any], model: str = MODEL) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("Extraction JSON invalide")
    units = []
    for index, raw in enumerate(data.get("units") or [], 1):
        if not isinstance(raw, dict) or str(raw.get("status") or "").upper() == "REJECTED":
            continue
        fact = str(raw.get("fact") or "").strip()
        if not fact:
            continue
        u = {"id": f"U{index:05d}", "page": raw.get("page"), "fact": fact,
             "quote": raw.get("quote") or "", "kind": raw.get("kind"),
             "geography": raw.get("geography"), "period": raw.get("period"),
             "status": raw.get("status") or "NEEDS_REVIEW",
             "reason": raw.get("reason"), "match_score": raw.get("match_score")}
        units.append(u)
    if not units:
        raise ValueError("Aucune unité exploitable")

    assignments = {}
    by_bucket = defaultdict(list)
    for u in units:
        theme = _theme(u["fact"], u.get("kind"))
        scope = _scope(u.get("geography"))
        assignments[u["id"]] = {"theme": theme, "scope": scope,
                                 "subtopic": str(u.get("kind") or "information").lower()}
        by_bucket[(scope, theme)].append(u)

    # Stable dossiers are an audit index, not an eligibility filter.
    dossiers = []
    for i, ((scope, theme), members) in enumerate(sorted(by_bucket.items()), 1):
        dossiers.append({"id": f"D{i:04d}", "theme": theme, "scope": scope,
                         "unit_ids": [u["id"] for u in members],
                         "unit_count": len(members),
                         "subtopics": dict(Counter(assignments[u["id"]]["subtopic"] for u in members))})
    dossier_ids = {(d["scope"], d["theme"]): d["id"] for d in dossiers}

    proposals = []
    # Group only facts in the same geography/theme, close in the PDF and in
    # the same period. Never use the grouping to manufacture a new conclusion.
    for (scope, theme), members in sorted(by_bucket.items()):
        ordered = sorted(members, key=lambda u: (_page(u) if _page(u) is not None else 10**9, u["id"]))
        groups: list[list[dict]] = []
        for u in ordered:
            if groups:
                last = groups[-1][-1]
                a, b = _page(last), _page(u)
                compatible_period = (not last.get("period") or not u.get("period")
                                     or str(last["period"]) == str(u["period"]))
                if (len(groups[-1]) < MAX_PER_CONTENT and a is not None and b is not None
                        and 0 <= b - a <= MAX_PAGE_GAP and compatible_period):
                    groups[-1].append(u)
                    continue
            groups.append([u])

        for group in groups:
            lead = group[0]
            evidence = group[:]
            ids = [u["id"] for u in evidence]
            # The original fact is the candidate title/angle. The later GENERATE
            # step may write an article but must not assert unsupported context.
            proposals.append({
                "title": _title(lead["fact"], scope),
                "angle": lead["fact"],
                "scope": scope,
                "editorial_rationale": ("Contenu source autonome à partir d'une unité extraite."
                    if len(evidence) == 1 else
                    f"Contenu source réunissant {len(evidence)} unités proches du même thème et territoire."),
                "unit_ids": ids,
                "dossier_id": dossier_ids[(scope, theme)],
                "pages": sorted({_page(u) for u in evidence if _page(u) is not None}),
                "evidence_count": len(evidence),
                "exact_quote_count": sum(u["status"] == "VERIFIED" for u in evidence),
                "review_count": sum(u["status"] != "VERIFIED" for u in evidence),
                "editorial_status": "REVIEW_REQUIRED",
                "evidence": evidence,
                "content_mode": "SOURCE_CONTENT",
            })

    proposals.sort(key=lambda p: (p["pages"][0] if p["pages"] else 10**9, p["title"]))
    for i, p in enumerate(proposals, 1):
        p["id"] = f"A{i:04d}"
    used = {u_id for p in proposals for u_id in p["unit_ids"]}
    uncovered = [u for u in units if u["id"] not in used]
    return {
        "document_hash": data.get("document_hash"),
        "document_title": data.get("document_title"),
        "source_id": data.get("source_id"), "model": model, "version": "5.0",
        "summary": {"input_units": len(units), "dossier_count": len(dossiers),
                    "article_proposals": len(proposals), "editorial_calls": 0,
                    "covered_units": len(used), "uncovered_units": len(uncovered),
                    "coverage_percent": round(100 * len(used) / len(units), 1),
                    "unit_statuses": dict(Counter(u["status"] for u in units))},
        "dossiers": dossiers, "assignments": assignments,
        "proposals": proposals, "uncovered_evidence": uncovered, "singletons": [],
        "note": "V5: contenus candidats d'acquisition, sans validation factuelle ni écriture en base."
    }
