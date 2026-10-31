"""PDF Studio V7 — PDF validation and page extraction only.

No LLM, database writes, topic classification or editorial segmentation.
All page numbers are 1-based.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import fitz

MAX_BYTES = 30 * 1024 * 1024
MAX_PAGES = 300
MIN_TEXT_CHARS = 80


def open_pdf(pdf_bytes: bytes) -> fitz.Document:
    if not pdf_bytes or len(pdf_bytes) > MAX_BYTES:
        raise ValueError("PDF vide ou supérieur à 30 Mo")
    if not pdf_bytes.startswith(b"%PDF"):
        raise ValueError("Le fichier fourni n'est pas un PDF")
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise ValueError("PDF illisible") from exc
    if doc.needs_pass or not 1 <= len(doc) <= MAX_PAGES:
        doc.close()
        raise ValueError("PDF protégé ou nombre de pages invalide")
    return doc


def document_metadata(doc: fitz.Document, pdf_bytes: bytes, filename: str) -> dict[str, Any]:
    metadata = doc.metadata or {}
    return {
        "document_hash": hashlib.sha256(pdf_bytes).hexdigest(),
        "filename": Path(filename).name,
        "page_count": len(doc),
        "title": metadata.get("title") or None,
        "author": metadata.get("author") or None,
    }


def extract_page(doc: fitz.Document, page_number: int) -> dict[str, Any]:
    if not 1 <= page_number <= len(doc):
        raise ValueError(f"Page hors limites : {page_number}")
    page = doc[page_number - 1]
    text = page.get_text("text", sort=True).replace("\u00a0", " ").strip()
    return {
        "page": page_number,
        "text": text,
        "char_count": len(text),
        "needs_visual_review": len(text) < MIN_TEXT_CHARS,
    }


def inspect_pdf(pdf_bytes: bytes, filename: str = "document.pdf") -> dict[str, Any]:
    """Lightweight inspection; no editorial decisions."""
    with open_pdf(pdf_bytes) as doc:
        pages = [extract_page(doc, n) for n in range(1, len(doc) + 1)]
        return {
            "status": "INSPECTED",
            "version": "7.0",
            "document": document_metadata(doc, pdf_bytes, filename),
            "pages": [
                {"page": p["page"], "char_count": p["char_count"],
                 "needs_visual_review": p["needs_visual_review"]}
                for p in pages
            ],
            "visual_review_pages": [p["page"] for p in pages if p["needs_visual_review"]],
        }
