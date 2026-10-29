"""PDF Studio V1 — inspect and map a PDF, without writing to BigQuery.

Dependencies: PyMuPDF (pip install pymupdf).
No LLM calls in this first stage. Page numbers are 1-based.
"""
from __future__ import annotations

import hashlib
import re
from collections import Counter
from pathlib import Path
from typing import Any

import fitz

MAX_PAGES = 300
MAX_BYTES = 30 * 1024 * 1024
MIN_PAGE_CHARS = 80

TOPICS = {
    "artificial_intelligence": [r"\bAI\b", r"artificial intelligence", r"agentic", r"machine learning"],
    "marketplaces": [r"marketplace", r"platform sellers?"],
    "payments": [r"payment", r"wallet", r"checkout", r"bancontact"],
    "logistics": [r"logistics", r"delivery", r"parcel", r"last.mile"],
    "regulation": [r"regulat", r"customs", r"compliance", r"legislation", r"tariff"],
    "sustainability": [r"sustainab", r"circular economy", r"recycl", r"resale"],
    "ecommerce_market": [r"e.commerce", r"e.shoppers?", r"turnover", r"web sales"],
}


def _normalize(text: str) -> str:
    return re.sub(r"[ \t]+", " ", (text or "").replace("\u00a0", " ")).strip()


def _load(pdf_bytes: bytes) -> fitz.Document:
    if not pdf_bytes or len(pdf_bytes) > MAX_BYTES:
        raise ValueError("PDF vide ou supérieur à 30 Mo")
    if not pdf_bytes.startswith(b"%PDF"):
        raise ValueError("Le fichier fourni n'est pas un PDF")
    try:
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise ValueError("PDF illisible") from exc
    if document.needs_pass:
        document.close()
        raise ValueError("PDF protégé par mot de passe")
    if not 1 <= len(document) <= MAX_PAGES:
        document.close()
        raise ValueError("Le PDF doit contenir entre 1 et 300 pages")
    return document


def inspect_pdf(pdf_bytes: bytes, filename: str = "document.pdf") -> dict[str, Any]:
    """Returns metadata, per-page extraction quality, and a stable document SHA256."""
    with _load(pdf_bytes) as doc:
        pages = []
        for index, page in enumerate(doc):
            text = _normalize(page.get_text("text", sort=True))
            image_count = len(page.get_images(full=True))
            pages.append({
                "page": index + 1,
                "char_count": len(text),
                "image_count": image_count,
                "needs_visual_review": len(text) < MIN_PAGE_CHARS or (image_count > 0 and len(text) < 400),
                "preview": text[:350],
            })
        metadata = doc.metadata or {}
        return {
            "document_hash": hashlib.sha256(pdf_bytes).hexdigest(),
            "filename": Path(filename).name,
            "page_count": len(doc),
            "title": metadata.get("title") or None,
            "author": metadata.get("author") or None,
            "pages": pages,
            "low_text_pages": [p["page"] for p in pages if p["char_count"] < MIN_PAGE_CHARS],
            "visual_review_pages": [p["page"] for p in pages if p["needs_visual_review"]],
        }


def map_pdf(pdf_bytes: bytes, filename: str = "document.pdf") -> dict[str, Any]:
    """Deterministic page/topic map; no editorial generation or AI assertions.

    Each topic reference points to the actual PDF page, not a fabricated citation.
    """
    overview = inspect_pdf(pdf_bytes, filename)
    compiled = {name: [re.compile(pattern, re.I) for pattern in patterns]
                for name, patterns in TOPICS.items()}
    topics: dict[str, list[dict[str, Any]]] = {name: [] for name in TOPICS}
    sections = []
    with _load(pdf_bytes) as doc:
        for index, page in enumerate(doc):
            page_no = index + 1
            text = _normalize(page.get_text("text", sort=True))
            lines = [s.strip() for s in text.splitlines() if s.strip()]
            heading = next((s for s in lines[:10] if 4 <= len(s) <= 95 and
                            not re.match(r"^\d+\s*[|/]", s)), None)
            if heading:
                sections.append({"page": page_no, "heading_candidate": heading})
            for name, patterns in compiled.items():
                count = sum(len(p.findall(text)) for p in patterns)
                if count:
                    topics[name].append({"page": page_no, "mentions": count})
    return {
        "document": {key: overview[key] for key in
                     ("document_hash", "filename", "page_count", "title", "author")},
        "quality": {"low_text_pages": overview["low_text_pages"],
                    "visual_review_pages": overview["visual_review_pages"]},
        "sections": sections,
        "topics": {key: {"page_count": len(pages), "pages": pages}
                   for key, pages in topics.items() if pages},
        "status": "MAPPED",
        "note": "Cartographie heuristique. Les titres et angles éditoriaux restent à valider avant génération.",
    }
