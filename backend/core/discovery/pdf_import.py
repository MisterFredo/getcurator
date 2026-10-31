
"""PDF Studio V7 — Import approved articles into GetCurator.

One editorial candidate produces one RAW article.

No atomic evidence units or consolidation.

Document traceability is preserved through page references
in RATECARD_CONTENT_DOCUMENT_EVIDENCE.

Imports are deterministic and retryable.
"""

from __future__ import annotations

import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from google.cloud import bigquery

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import get_bigquery_client


RAW = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_RAW"

DOC = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_SOURCE_DOCUMENT"
)

EVIDENCE = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_CONTENT_DOCUMENT_EVIDENCE"
)

MAX_ARTICLES = 100

PAGE_PATTERN = re.compile(
    r"\[p\.\s*(\d+)\]",
    re.IGNORECASE,
)


# ============================================================
# HELPERS
# ============================================================

def _text(value: Any) -> str:
    return str(value or "").strip()


def _query(
    client: bigquery.Client,
    sql: str,
    params: list | None = None,
):
    job = client.query(
        sql,
        job_config=bigquery.QueryJobConfig(
            query_parameters=params or [],
        ),
    )

    return list(job.result())


def _param(name: str, value: str):
    return bigquery.ScalarQueryParameter(
        name,
        "STRING",
        value,
    )


def _pages_from_text(text: str) -> list[int]:
    return sorted({
        int(value)
        for value in PAGE_PATTERN.findall(text or "")
    })


def _source_page_numbers(article: dict) -> set[int]:
    pages = article.get("source_pages") or []

    if not isinstance(pages, list):
        raise ValueError(
            "source_pages doit être une liste."
        )

    result = set()

    for item in pages:

        if not isinstance(item, dict):
            raise ValueError(
                "Page source invalide."
            )

        number = item.get("page")

        if (
            isinstance(number, bool)
            or not isinstance(number, int)
            or number < 1
        ):
            raise ValueError(
                "Numéro de page source invalide."
            )

        if number in result:
            raise ValueError(
                "Page source dupliquée."
            )

        result.add(number)

    return result


# ============================================================
# DOCUMENT
# ============================================================

def _get_document(
    client: bigquery.Client,
    document_id: str,
):
    rows = _query(
        client,
        f"""
        SELECT
            ID_DOCUMENT,
            ID_SOURCE,
            SHA256,
            TITLE,
            STORAGE_URI
        FROM `{DOC}`
        WHERE ID_DOCUMENT = @id
        LIMIT 1
        """,
        [_param("id", document_id)],
    )

    if not rows:
        raise ValueError(
            "Document PDF non enregistré."
        )

    return rows[0]


# ============================================================
# ARTICLE VALIDATION
# ============================================================

def _validate_article(
    article: dict,
    document: Any,
) -> dict:
    if not isinstance(article, dict):
        raise ValueError(
            "Format d'article invalide."
        )

    if article.get("status") != "APPROVED":
        raise ValueError(
            "L'article doit être approuvé "
            "avant son import."
        )

    if article.get("version") != "7.0":
        raise ValueError(
            "Seuls les articles PDF Studio V7 "
            "sont acceptés."
        )

    proposal_id = _text(
        article.get("proposal_id")
    )

    if not proposal_id:
        raise ValueError(
            "Identifiant du candidat manquant."
        )

    if (
        _text(article.get("source_id"))
        != _text(document.ID_SOURCE)
    ):
        raise ValueError(
            "La source de l'article ne correspond "
            "pas à celle du document."
        )

    if (
        _text(article.get("document_hash"))
        != _text(document.SHA256)
    ):
        raise ValueError(
            "Le document source ne correspond "
            "pas au PDF enregistré."
        )

    title = _text(article.get("title"))
    excerpt = _text(article.get("excerpt"))
    body = _text(article.get("body"))

    if not title or not excerpt or not body:
        raise ValueError(
            "Titre, extrait et corps obligatoires."
        )

    allowed_pages = _source_page_numbers(
        article
    )

    if not allowed_pages:
        raise ValueError(
            "Pages sources manquantes."
        )

    cited_pages = _pages_from_text(
        body
    )

    if not cited_pages:
        raise ValueError(
            "L'article doit citer ses pages sources."
        )

    invalid = set(cited_pages) - allowed_pages

    if invalid:
        raise ValueError(
            "Pages citées absentes du candidat : "
            + ", ".join(
                str(n) for n in sorted(invalid)
            )
        )

    key_points = article.get("key_points") or []

    if not isinstance(key_points, list):
        raise ValueError(
            "key_points doit être une liste."
        )

    normalized_points = []

    for point in key_points:

        if not isinstance(point, str):
            raise ValueError(
                "Point clé invalide."
            )

        value = point.strip()

        if not value:
            continue

        point_pages = _pages_from_text(value)

        if not point_pages:
            raise ValueError(
                "Chaque point clé doit citer "
                "au moins une page."
            )

        if set(point_pages) - allowed_pages:
            raise ValueError(
                "Un point clé cite une page "
                "absente du candidat."
            )

        normalized_points.append(value)

    all_cited_pages = sorted(
        set(cited_pages)
        | {
            page
            for point in normalized_points
            for page in _pages_from_text(point)
        }
    )

    # RAW_TEXT remains compatible with the existing
    # GetCurator analysis pipeline.
    #
    # Key points are included explicitly, but no
    # additional structured columns are required.

    sections = [
        title,
        excerpt,
    ]

    if normalized_points:
        sections.append(
            "Principaux enseignements\n"
            + "\n".join(
                f"- {point}"
                for point in normalized_points
            )
        )

    sections.append(body)

    return {
        "proposal_id": proposal_id,
        "title": title,
        "excerpt": excerpt,
        "body": body,
        "key_points": normalized_points,
        "raw_text": "\n\n".join(sections),
        "cited_pages": all_cited_pages,
    }


# ============================================================
# EXISTING RAW
# ============================================================

def _existing_raw(
    client: bigquery.Client,
    raw_id: str,
):
    rows = _query(
        client,
        f"""
        SELECT
            ID_RAW,
            SOURCE_URL
        FROM `{RAW}`
        WHERE ID_RAW = @id
        LIMIT 1
        """,
        [_param("id", raw_id)],
    )

    return rows[0] if rows else None


# ============================================================
# INSERT PAGE REFERENCES
# ============================================================

def _ensure_page_references(
    client: bigquery.Client,
    document_id: str,
    raw_id: str,
    proposal_id: str,
    pages: list[int],
):
    """Persist page-level provenance.

    These are page references, not verified factual
    evidence units.

    MERGE prevents duplicates on retry.
    """

    for page in pages:

        unit_id = f"PAGE_{page:04d}"

        sql = f"""
        MERGE `{EVIDENCE}` AS target

        USING (
            SELECT
                @raw_id AS ID_RAW,
                @document_id AS ID_DOCUMENT,
                @proposal_id AS ARTICLE_ID,
                @unit_id AS UNIT_ID,
                @page AS PDF_PAGE
        ) AS source

        ON target.ID_RAW = source.ID_RAW
        AND target.ID_DOCUMENT = source.ID_DOCUMENT
        AND target.UNIT_ID = source.UNIT_ID

        WHEN NOT MATCHED THEN
            INSERT (
                ID_RAW,
                ID_DOCUMENT,
                ARTICLE_ID,
                UNIT_ID,
                PDF_PAGE,
                QUOTE,
                FACT,
                VERIFICATION_STATUS,
                CREATED_AT
            )
            VALUES (
                source.ID_RAW,
                source.ID_DOCUMENT,
                source.ARTICLE_ID,
                source.UNIT_ID,
                source.PDF_PAGE,
                '',
                '',
                'PAGE_REFERENCE_ONLY',
                CURRENT_TIMESTAMP()
            )
        """

        _query(
            client,
            sql,
            [
                _param("raw_id", raw_id),
                _param("document_id", document_id),
                _param("proposal_id", proposal_id),
                _param("unit_id", unit_id),
                bigquery.ScalarQueryParameter(
                    "page",
                    "INT64",
                    page,
                ),
            ],
        )


# ============================================================
# INSERT RAW
# ============================================================

def _ensure_raw(
    client: bigquery.Client,
    raw_id: str,
    source_id: str,
    source_url: str,
    article: dict,
) -> bool:
    """Create RAW article only if absent.

    Returns True when it already existed.
    """

    existing = _existing_raw(
        client,
        raw_id,
    )

    if existing:

        if existing.SOURCE_URL != source_url:
            raise ValueError(
                "Conflit d'identifiant RAW."
            )

        return True

    sql = f"""
    MERGE `{RAW}` AS target

    USING (
        SELECT
            @raw_id AS ID_RAW,
            @source_id AS SOURCE_ID,
            @raw_text AS RAW_TEXT,
            @title AS SOURCE_TITLE,
            @source_url AS SOURCE_URL
    ) AS source

    ON target.ID_RAW = source.ID_RAW

    WHEN NOT MATCHED THEN
        INSERT (
            ID_RAW,
            SOURCE_ID,
            RAW_TEXT,
            SOURCE_TITLE,
            SOURCE_URL,
            IMPORT_TYPE,
            STATUS,
            CREATED_AT
        )
        VALUES (
            source.ID_RAW,
            source.SOURCE_ID,
            source.RAW_TEXT,
            source.SOURCE_TITLE,
            source.SOURCE_URL,
            'PDF',
            'STORED',
            CURRENT_TIMESTAMP()
        )
    """

    _query(
        client,
        sql,
        [
            _param("raw_id", raw_id),
            _param("source_id", source_id),
            _param(
                "raw_text",
                article["raw_text"],
            ),
            _param(
                "title",
                article["title"],
            ),
            _param(
                "source_url",
                source_url,
            ),
        ],
    )

    return False


# ============================================================
# IMPORT APPROVED ARTICLES
# ============================================================

def import_approved(payload: dict) -> dict:
    """Import reviewed V7 articles into RATECARD_CONTENT_RAW."""

    document_id = _text(
        payload.get("id_document")
    )

    articles = payload.get("articles")

    if not document_id:
        raise ValueError(
            "id_document obligatoire."
        )

    if (
        not isinstance(articles, list)
        or not 1 <= len(articles) <= MAX_ARTICLES
    ):
        raise ValueError(
            f"Entre 1 et {MAX_ARTICLES} articles "
            "validés sont requis."
        )

    base = os.getenv(
        "PDF_STUDIO_ARTICLE_BASE_URL",
        "",
    ).strip().rstrip("/")

    if not base.startswith("https://"):
        raise ValueError(
            "PDF_STUDIO_ARTICLE_BASE_URL "
            "doit être une URL HTTPS."
        )

    client = get_bigquery_client()

    document = _get_document(
        client,
        document_id,
    )

    # Validate everything before the first write.

    validated = []
    seen = set()

    for item in articles:

        article = _validate_article(
            item,
            document,
        )

        proposal_id = article["proposal_id"]

        if proposal_id in seen:
            raise ValueError(
                "Candidat présent plusieurs fois "
                "dans le même import."
            )

        seen.add(proposal_id)

        stable_id = str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"{document_id}:{proposal_id}",
            )
        )

        source_url = (
            f"{base}/pdf-source/{stable_id}"
        )

        validated.append({
            **article,
            "id_raw": stable_id,
            "source_url": source_url,
        })

    # --------------------------------------------------------
    # IMPORT
    # --------------------------------------------------------

    results = []

    for article in validated:

        raw_id = article["id_raw"]

        # Page references first.
        #
        # A retry can complete a partially failed import
        # without duplicating existing references.

        _ensure_page_references(
            client=client,
            document_id=document_id,
            raw_id=raw_id,
            proposal_id=article["proposal_id"],
            pages=article["cited_pages"],
        )

        already_exists = _ensure_raw(
            client=client,
            raw_id=raw_id,
            source_id=document.ID_SOURCE,
            source_url=article["source_url"],
            article=article,
        )

        results.append({
            "proposal_id": article["proposal_id"],
            "id_raw": raw_id,
            "source_url": article["source_url"],
            "already_exists": already_exists,
            "cited_pages": article["cited_pages"],
        })

    return {
        "status": "IMPORTED",
        "version": "7.0",
        "id_document": document_id,
        "articles": results,
        "count": len(results),
    }


# ============================================================
# GET PDF ARTICLE
# ============================================================

def get_pdf_article(id_raw: str) -> dict:
    """Retrieve imported article and original PDF provenance."""

    client = get_bigquery_client()

    rows = _query(
        client,
        f"""
        SELECT
            r.ID_RAW,
            r.SOURCE_TITLE,
            r.RAW_TEXT,
            r.SOURCE_ID,
            r.SOURCE_URL,
            d.TITLE AS DOCUMENT_TITLE,
            d.STORAGE_URI,
            d.ID_DOCUMENT

        FROM `{RAW}` r

        JOIN `{EVIDENCE}` e
            ON e.ID_RAW = r.ID_RAW

        JOIN `{DOC}` d
            ON d.ID_DOCUMENT = e.ID_DOCUMENT

        WHERE
            r.ID_RAW = @id
            AND r.IMPORT_TYPE = 'PDF'

        LIMIT 1
        """,
        [_param("id", id_raw)],
    )

    if not rows:
        raise ValueError(
            "Article documentaire introuvable."
        )

    article = rows[0]

    references = _query(
        client,
        f"""
        SELECT
            UNIT_ID,
            PDF_PAGE,
            QUOTE,
            FACT,
            VERIFICATION_STATUS

        FROM `{EVIDENCE}`

        WHERE ID_RAW = @id

        ORDER BY PDF_PAGE, UNIT_ID
        """,
        [_param("id", id_raw)],
    )

    # Reuse existing GCS media configuration.
    # Public URL is only returned for storage URIs
    # belonging to the configured media bucket.

    from utils.gcs import (
        BASE_URL,
        BUCKET_NAME,
    )

    prefix = f"gs://{BUCKET_NAME}/"

    storage_uri = _text(
        article.STORAGE_URI
    )

    pdf_url = None

    if storage_uri.startswith(prefix):
        pdf_url = (
            f"{BASE_URL.rstrip('/')}/"
            f"{storage_uri[len(prefix):]}"
        )

    pages = sorted({
        row.PDF_PAGE
        for row in references
        if row.PDF_PAGE is not None
    })

    return {
        "id_raw": article.ID_RAW,
        "title": article.SOURCE_TITLE,
        "body": article.RAW_TEXT,
        "source_id": article.SOURCE_ID,
        "source_url": article.SOURCE_URL,
        "id_document": article.ID_DOCUMENT,
        "document_title": article.DOCUMENT_TITLE,
        "pdf_url": pdf_url,
        "pages": pages,
        "evidence": [
            {
                "unit_id": row.UNIT_ID,
                "page": row.PDF_PAGE,
                "quote": row.QUOTE,
                "fact": row.FACT,
                "verification_status": (
                    row.VERIFICATION_STATUS
                ),
            }
            for row in references
        ],
    }
