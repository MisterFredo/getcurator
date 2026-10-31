"""PDF Studio V6 — conservative, document-first segmentation.

No LLM, persistence or article generation. Sections are page-bounded;
subtopics are candidate excerpts based on PDF text blocks and must be reviewed.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import fitz

MAX_BYTES = 30 * 1024 * 1024
MAX_PAGES = 300

REGIONS = {"WESTERN EUROPE", "NORTHERN EUROPE", "CENTRAL EUROPE", "EASTERN EUROPE", "SOUTHERN EUROPE"}
COUNTRIES = {"Albania", "Austria", "Belgium", "Bosnia and Herzegovina", "Bulgaria", "Croatia", "Cyprus", "Czech Republic", "Denmark", "Estonia", "Finland", "France", "Germany", "Greece", "Hungary", "Iceland", "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg", "Malta", "Moldova", "Montenegro", "Netherlands", "North Macedonia", "Norway", "Poland", "Portugal", "Romania", "Serbia", "Slovak Republic", "Slovenia", "Spain", "Sweden", "Switzerland", "Ukraine", "United Kingdom"}
HEADINGS = {"Policies and regulation": "regulation", "Sustainability": "sustainability", "Technology": "technology", "e-Payments": "payments", "e-Logistics": "logistics", "Other areas related to e-commerce": "consumer_behavior"}
ALIASES = {"Netherlands": ["Netherlands", "Dutch", "Pays-Bas", "néerlandais"], "United Kingdom": ["United Kingdom", "British", "UK"], "Germany": ["Germany", "German"], "France": ["France", "French"], "Belgium": ["Belgium", "Belgian"]}


def _clean(s: str) -> str:
    return re.sub(r"[ \t]+", " ", (s or "").replace("\u00a0", " ")).strip()


def _open(data: bytes):
    if not data or len(data) > MAX_BYTES or not data.startswith(b"%PDF"):
        raise ValueError("PDF invalide ou supérieur à 30 Mo")
    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise ValueError("PDF illisible") from exc
    if doc.needs_pass or not 1 <= len(doc) <= MAX_PAGES:
        doc.close()
        raise ValueError("PDF protégé ou nombre de pages invalide")
    return doc


def _page_blocks(page):
    blocks = []
    for b in page.get_text("blocks", sort=False):
        if len(b) < 7 or b[6] != 0:
            continue
        text = _clean(b[4])
        if text:
            blocks.append({"bbox": [round(float(v), 1) for v in b[:4]], "text": text})
    return blocks


def _heading_candidates(blocks):
    found = []
    for b in blocks:
        for line in b["text"].splitlines():
            line = _clean(line)
            if line in HEADINGS:
                found.append({"heading": line, "topic": HEADINGS[line], "bbox": b["bbox"]})
    return found


def _boundaries(doc):
    # Prefer running headers for this report, but use bookmarks for generic PDFs.
    entries = [{"page": 1, "title": "Cover", "kind": "front", "level": 1, "origin": "first_page"}]
    previous = None
    recognized = 0
    for i, page in enumerate(doc):
        lines = [x.strip() for x in page.get_text("text", sort=True).splitlines() if x.strip()]
        header = next((x for x in lines[:4] if re.match(r"^\d+\s*\|", x)), "")
        parts = [p.strip() for p in header.split("|")]
        if len(parts) < 3:
            continue
        if len(parts) >= 4 and parts[-1] in COUNTRIES:
            kind, title = "country", parts[-1]
        elif parts[-1].upper() in REGIONS:
            kind, title = "region", parts[-1]
        elif parts[-1].lower() in {"contents", "introduction", "copyright"}:
            kind, title = "front", parts[-1]
        else:
            kind, title = "overview", parts[-1]
        key = (kind, title)
        if key != previous:
            entries.append({"page": i + 1, "title": title, "kind": kind, "level": 2 if kind == "country" else 1, "origin": "running_header"})
            previous = key
            recognized += 1
    if recognized >= 8:
        return entries
    bookmarks = [{"page": p, "title": t.strip(), "kind": "bookmark", "level": level, "origin": "pdf_bookmark"} for level, t, p in doc.get_toc() if 1 <= p <= len(doc) and t.strip()]
    if bookmarks:
        return [entries[0]] + bookmarks
    return entries


def _mentions(text: str, primary: str | None):
    matches = []
    for country in sorted(COUNTRIES):
        names = ALIASES.get(country, [country])
        patterns = [re.compile(r"(?<!\w)" + re.escape(n) + r"(?!\w)", re.I) for n in names]
        count = sum(len(p.findall(text)) for p in patterns)
        if count:
            matches.append({"country": country, "mentions": count, "role": "PRIMARY" if country == primary else "MENTIONED", "verification": "TEXT_MATCH_ONLY"})
    return matches


def segment_pdf(pdf_bytes: bytes, filename: str = "document.pdf") -> dict[str, Any]:
    with _open(pdf_bytes) as doc:
        entries = _boundaries(doc)
        # Same-page bookmarks are metadata; do not create overlapping page ranges.
        starts = sorted({e["page"] for e in entries})
        segments = []
        for i, start in enumerate(starts):
            end = starts[i + 1] - 1 if i + 1 < len(starts) else len(doc)
            at_start = [e for e in entries if e["page"] == start]
            entry = at_start[-1]
            pages = []
            subtopics = []
            for n in range(start, end + 1):
                page = doc[n - 1]
                blocks = _page_blocks(page)
                page_text = _clean(page.get_text("text", sort=True))
                pages.append({"page": n, "text": page_text, "blocks": blocks})
                for h in _heading_candidates(blocks):
                    subtopics.append({"page": n, **h})
            primary = entry["title"] if entry["kind"] == "country" else None
            body = "\n".join(p["text"] for p in pages)
            segments.append({"id": f"S{len(segments)+1:04d}", "title": entry["title"], "kind": entry["kind"], "start_page": start, "end_page": end, "country_primary": primary, "pages": pages, "same_page_headings": at_start, "subtopic_candidates": subtopics, "country_mentions": _mentions(body, primary), "review_status": "NEEDS_REVIEW"})
        covered = {p["page"] for s in segments for p in s["pages"]}
        return {"status": "SEGMENTED_CANDIDATES", "version": "6.2", "document": {"document_hash": hashlib.sha256(pdf_bytes).hexdigest(), "filename": Path(filename).name, "page_count": len(doc)}, "summary": {"segments": len(segments), "pages_covered": len(covered), "uncovered_pages": sorted(set(range(1, len(doc)+1))-covered)}, "sections": entries, "segments": segments, "warnings": ["Rubriques détectées mais non isolées en extraits fiables", "Les mentions géographiques sont lexicales, non exhaustives pour les tableaux et graphiques"]}


def build_document_candidates(pdf_bytes: bytes, filename: str = "document.pdf") -> dict[str, Any]:
    result = segment_pdf(pdf_bytes, filename)
    candidates = []
    for seg in result["segments"]:
        if seg["kind"] == "front":
            continue
        candidates.append({"id": f"C{len(candidates)+1:04d}", "source_segment_id": seg["id"], "title": seg["title"], "kind": seg["kind"], "start_page": seg["start_page"], "end_page": seg["end_page"], "country_primary": seg["country_primary"], "country_mentions": seg["country_mentions"], "subtopic_candidates": seg["subtopic_candidates"], "source_pages": seg["pages"], "review_status": "NEEDS_REVIEW", "generatable": False})
    return {"status": "DOCUMENT_CANDIDATES_REVIEW", "version": result["version"], "document": result["document"], "summary": {**result["summary"], "candidates": len(candidates)}, "candidates": candidates, "warnings": result["warnings"]}

# ---------------------------------------------------------------------------
# V6.4 — Editorial passages reconstructed from positioned PDF text blocks.
# Conservative: proposals only; never silently approve or import.
# ---------------------------------------------------------------------------

def _editorial_blocks(page, number: int) -> list[dict[str, Any]]:
    """Reading order by column, then top-to-bottom, for multi-column pages.

    Text is kept verbatim (apart from whitespace normalization). Bounding boxes
    permit manual inspection of ambiguous fragments.
    """
    width, height = float(page.rect.width), float(page.rect.height)
    raw = _page_blocks(page)
    body = []
    for b in raw:
        x0, y0, x1, y1 = b['bbox']
        text = b['text']
        if y0 < height * 0.15 or y0 > height * 0.945:
            continue  # running headers, page number, continuation footers
        if re.match(r'(?i)^continued (?:from|on) (?:previous|the next) page', text):
            continue
        if re.match(r'(?i)^(interview|managing director\b)', text):
            continue
        # Pull quotes are visual duplication, not part of the linear interview.
        if text.lstrip().startswith(('“', '"')) and len(text) < 420:
            continue
        body.append({'page': number, 'bbox': b['bbox'], 'text': text,
                     'x_center': (x0 + x1) / 2})
    # Estimate a column for each block. Works for 2- and 3-column landscape pages;
    # avoid splitting a full-width text block into an arbitrary column.
    for b in body:
        x0, _, x1, _ = b['bbox']
        b['column'] = None if x1 - x0 > width * .55 else min(2, int(b['x_center'] / (width / 3)))
    return sorted(body, key=lambda b: (b['column'] if b['column'] is not None else -1,
                                       b['bbox'][1], b['bbox'][0]))


def _split_heading(text: str) -> tuple[str | None, str | None, str]:
    """Split only an explicitly recognized heading at the start of a block."""
    for heading, topic in sorted(HEADINGS.items(), key=lambda x: -len(x[0])):
        match = re.match(r'^' + re.escape(heading) + r'(?=\s|$)', text, re.I)
        if match:
            return heading, topic, text[match.end():].strip()
    return None, None, text


def _editorial_for_segment(doc, segment: dict[str, Any]) -> list[dict[str, Any]]:
    """Assemble heading-bounded passages, allowing continuation across pages."""
    if segment.get('kind') != 'country':
        return []
    blocks = []
    for page_no in range(segment['start_page'], segment['end_page'] + 1):
        blocks.extend(_editorial_blocks(doc[page_no - 1], page_no))

    # Preserve source ordering within the country chapter, never reorder by topic.
    passages = []
    current = None
    preamble = []
    for block in blocks:
        heading, topic, rest = _split_heading(block['text'])
        if heading:
            if current is not None:
                passages.append(current)
            current = {'topic': topic, 'heading': heading, 'blocks': [],
                       'source_segment_id': segment['id']}
            if rest:
                current['blocks'].append({**block, 'text': rest})
        elif current is not None:
            current['blocks'].append(block)
        else:
            preamble.append(block)

    if current is not None:
        passages.append(current)

    # Intro/statistical pages and pre-heading text remain reviewable rather than
    # being silently assigned to the first topic.
    if preamble:
        passages.insert(0, {'topic': 'unclassified', 'heading': 'Unclassified / statistics',
                            'blocks': preamble, 'source_segment_id': segment['id']})
    return passages


def build_editorial_candidates(pdf_bytes: bytes, filename: str = 'document.pdf',
                               country: str | None = None) -> dict[str, Any]:
    """Return topic-level editorial proposals with traceable, ordered text blocks.

    Optional country filter allows small, targeted tests without processing
    every country in the report. This is not semantic extraction or validation.
    """
    result = segment_pdf(pdf_bytes, filename)
    with _open(pdf_bytes) as doc:
        candidates = []
        for seg in result['segments']:
            if seg.get('kind') != 'country':
                continue
            if country and seg.get('country_primary', '').casefold() != country.casefold():
                continue
            for passage in _editorial_for_segment(doc, seg):
                if not passage['blocks']:
                    continue
                by_page = {}
                for b in passage['blocks']:
                    by_page.setdefault(b['page'], []).append(b['text'])
                pages = [{'page': n, 'text': '\n\n'.join(parts)}
                         for n, parts in sorted(by_page.items())]
                candidates.append({
                    'id': f'E{len(candidates)+1:04d}',
                    'source_segment_id': seg['id'],
                    'title': f"{seg['title']} — {passage['heading']}",
                    'kind': 'editorial_candidate',
                    'topic': passage['topic'],
                    'country_primary': seg['country_primary'],
                    'start_page': pages[0]['page'],
                    'end_page': pages[-1]['page'],
                    'pages': pages,
                    'source_blocks': passage['blocks'],
                    'review_status': 'NEEDS_REVIEW',
                    'generatable': False,
                    'warnings': (["Passage non classé : vérifier les graphiques, tableaux et titres."]
                                 if passage['topic'] == 'unclassified' else
                                 ["Ordre reconstruit par colonnes : vérifier visuellement les transitions et citations."]),
                })
    return {
        'status': 'EDITORIAL_CANDIDATES_REVIEW', 'version': '6.4',
        'document': result['document'],
        'summary': {'candidates': len(candidates), 'pages_covered_structurally': result['summary']['pages_covered']},
        'candidates': candidates,
        'warnings': ['Extraction heuristique des colonnes : non garantie pour tous les PDF.',
                     'Les titres ne sont reconnus que pour le vocabulaire de rubriques configuré.',
                     'Chaque candidat nécessite une validation humaine avant génération.'],
    }
