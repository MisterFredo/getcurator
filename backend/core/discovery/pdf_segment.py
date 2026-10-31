
"""PDF Studio V7 — document structure to article candidates.

One coherent editorial unit becomes one article candidate.
A country section such as Netherlands (pp. 32–35) is ONE
candidate, not one per subheading.

No LLM, no persistence and no topic/paragraph segmentation.
"""

from __future__ import annotations

import re
from typing import Any

from core.discovery.pdf_studio import (
    document_metadata,
    extract_page,
    open_pdf,
)


FRONT_TITLES = {
    "cover",
    "contents",
    "table of contents",
    "introduction",
    "copyright",
    "methodology",
}

REGION_TITLES = {
    "western europe",
    "northern europe",
    "central europe",
    "eastern europe",
    "southern europe",
}


# ============================================================
# RUNNING HEADER
# ============================================================

def _running_header(
    page: Any,
) -> tuple[str, str, str | None] | None:
    """Recognize the report's running headers.

    Example:
    32 | European E-commerce Report 2026 |
    Western Europe | Netherlands

    Returns:
        (title, kind, parent)

    Generic PDFs fall back to bookmarks.
    """

    lines = [
        s.strip()
        for s in page.get_text(
            "text",
            sort=True,
        ).splitlines()
        if s.strip()
    ]

    for line in lines[:6]:

        if not re.match(
            r"^\d+\s*\|",
            line,
        ):
            continue

        parts = [
            p.strip()
            for p in line.split("|")
        ]

        if len(parts) < 3:
            continue

        title = parts[-1]

        parent = (
            parts[-2]
            if len(parts) >= 4
            else None
        )

        if title.casefold() in FRONT_TITLES:
            return title, "front", None

        if title.casefold() in REGION_TITLES:
            return title, "region", None

        if (
            parent
            and parent.casefold() in REGION_TITLES
        ):
            return title, "country", parent

        return title, "section", parent

    return None


# ============================================================
# DOCUMENT STRUCTURE
# ============================================================

def _entries(
    doc: Any,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Prefer consistent running headers.

    Otherwise use PDF bookmarks.
    """

    detected = []

    for n, page in enumerate(doc, 1):

        match = _running_header(page)

        if not match:
            continue

        title, kind, parent = match

        detected.append({
            "page": n,
            "title": title,
            "kind": kind,
            "parent": parent,
            "origin": "running_header",
        })

    unique_titles = {
        e["title"].casefold()
        for e in detected
    }

    if (
        len(detected) >= max(
            5,
            len(doc) // 3,
        )
        and len(unique_titles) >= 5
    ):

        entries = []
        previous_key = None

        for entry in detected:

            key = (
                entry["title"].casefold(),
                entry["kind"],
            )

            if key != previous_key:

                entries.append(entry)

                previous_key = key

        return entries, []

    # --------------------------------------------------------
    # PDF BOOKMARKS
    # --------------------------------------------------------

    toc = doc.get_toc()

    if toc:

        entries = [
            {
                "page": page,
                "title": title.strip(),
                "kind": "section",
                "parent": None,
                "level": level,
                "origin": "bookmark",
            }
            for level, title, page in toc
            if (
                title.strip()
                and 1 <= page <= len(doc)
            )
        ]

        if entries:

            deepest = max(
                e["level"]
                for e in entries
            )

            chosen = [
                e
                for e in entries
                if e["level"] == deepest
            ]

            if chosen:

                return chosen, [
                    "Découpage fondé sur les signets : "
                    "vérifier les unités proposées."
                ]

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    return [
        {
            "page": 1,
            "title": "Document",
            "kind": "document",
            "parent": None,
            "origin": "fallback",
        }
    ], [
        "Aucune structure fiable détectée : "
        "un seul candidat pour le document."
    ]


# ============================================================
# ARTICLE CANDIDATES
# ============================================================

def segment_pdf(
    pdf_bytes: bytes,
    filename: str = "document.pdf",
) -> dict[str, Any]:
    """Propose article candidates with source pages.

    Page ranges are non-overlapping.

    Editorial boundaries within the same PDF page
    are not guessed.

    Candidates must be reviewed before generation/import.
    """

    with open_pdf(pdf_bytes) as doc:

        document = document_metadata(
            doc,
            pdf_bytes,
            filename,
        )

        entries, warnings = _entries(doc)

        entries = sorted(
            entries,
            key=lambda e: e["page"],
        )

        # ----------------------------------------------------
        # PAGE BOUNDARIES
        # ----------------------------------------------------

        by_start = {}

        for entry in entries:

            if entry["page"] in by_start:

                warnings.append(
                    "Plusieurs sections commencent "
                    f"page {entry['page']} : "
                    "revue nécessaire."
                )

            by_start[entry["page"]] = entry

        starts = sorted(by_start)

        if not starts or starts[0] > 1:

            warnings.append(
                "Pages avant la première section : "
                "non attribuées à un article."
            )

        candidates = []
        excluded = []

        # ----------------------------------------------------
        # BUILD CANDIDATES
        # ----------------------------------------------------

        for index, start in enumerate(starts):

            entry = by_start[start]

            end = (
                starts[index + 1] - 1
                if index + 1 < len(starts)
                else len(doc)
            )

            if entry["kind"] == "front":

                excluded.extend(
                    range(
                        start,
                        end + 1,
                    )
                )

                continue

            pages = [
                extract_page(doc, n)
                for n in range(
                    start,
                    end + 1,
                )
            ]

            candidates.append({
                "id": (
                    f"C{len(candidates) + 1:04d}"
                ),
                "title": entry["title"],
                "kind": entry["kind"],
                "parent": entry.get("parent"),
                "start_page": start,
                "end_page": end,
                "pages": [
                    {
                        "page": p["page"],
                        "text": p["text"],
                    }
                    for p in pages
                ],
                "visual_review_pages": [
                    p["page"]
                    for p in pages
                    if p["needs_visual_review"]
                ],
                "review_status": "NEEDS_REVIEW",
            })

        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------

        return {
            "status": "ARTICLE_CANDIDATES_REVIEW",
            "version": "7.0",
            "document": document,
            "summary": {
                "candidates": len(candidates),
                "excluded_pages": excluded,
                "candidate_pages": sum(
                    c["end_page"]
                    - c["start_page"]
                    + 1
                    for c in candidates
                ),
            },
            "candidates": candidates,
            "warnings": list(
                dict.fromkeys(warnings)
            ),
        }
