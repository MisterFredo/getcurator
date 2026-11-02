"""Cross-document, read-only search for PDF Studio documentary library.

No editorial mutation and no RATECARD_CONTENT_RAW creation.
"""
from google.cloud import bigquery
from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import get_bigquery_client

ROOT = f"{BQ_PROJECT}.{BQ_DATASET}"
TOPIC = f"{ROOT}.RATECARD_DOCUMENT_TOPIC"
UNIT = f"{ROOT}.RATECARD_DOCUMENT_UNIT"
LINK = f"{ROOT}.RATECARD_DOCUMENT_TOPIC_UNIT"
DOCUMENT = f"{ROOT}.RATECARD_SOURCE_DOCUMENT"


def _search_params(query, document_id, quality_status, editorial_status, limit, offset, *, topics):
    if not isinstance(limit, int) or not 1 <= limit <= 100 or not isinstance(offset, int) or offset < 0:
        raise ValueError("Pagination invalide (limit 1–100, offset >= 0).")
    query = (query or "").strip()
    if len(query) > 300:
        raise ValueError("Recherche trop longue (300 caractères maximum).")
    if quality_status and quality_status not in ("ACCEPTED", "REJECTED", "PENDING"):
        raise ValueError("Statut qualité invalide.")
    if editorial_status and editorial_status not in ("REVIEW", "SELECTED", "IGNORED"):
        raise ValueError("Statut éditorial invalide.")
    alias = "t" if topics else "u"
    where = []
    params = [bigquery.ScalarQueryParameter("limit", "INT64", limit),
              bigquery.ScalarQueryParameter("offset", "INT64", offset)]
    if query:
        fields = [f"{alias}.TITLE", f"{alias}.ANGLE", f"{alias}.EDITORIAL_RATIONALE"] if topics else [f"{alias}.FACT", f"{alias}.QUOTE"]
        where.append("(" + " OR ".join(f"CONTAINS_SUBSTR({f}, @query)" for f in fields) + ")")
        params.append(bigquery.ScalarQueryParameter("query", "STRING", query))
    if document_id:
        where.append(f"{alias}.ID_DOCUMENT = @document_id")
        params.append(bigquery.ScalarQueryParameter("document_id", "STRING", document_id))
    if quality_status:
        if not topics:
            raise ValueError("Le filtre qualité ne s'applique qu'aux sujets.")
        if quality_status == "PENDING":
            where.append("t.QUALITY_VALIDATED_AT IS NULL")
        else:
            where.append("t.QUALITY_VALIDATED_AT IS NOT NULL AND t.QUALITY_STATUS = @quality_status")
            params.append(bigquery.ScalarQueryParameter("quality_status", "STRING", quality_status))
    if editorial_status:
        if not topics:
            raise ValueError("Le filtre éditorial ne s'applique qu'aux sujets.")
        where.append("t.EDITORIAL_STATUS = @editorial_status")
        params.append(bigquery.ScalarQueryParameter("editorial_status", "STRING", editorial_status))
    return ("WHERE " + " AND ".join(where)) if where else "", params


def _run(sql, params):
    job = get_bigquery_client().query(sql, job_config=bigquery.QueryJobConfig(query_parameters=params))
    return [dict(row.items()) for row in job.result()]


def search_library_topics(query=None, document_id=None, quality_status=None, editorial_status=None, limit=50, offset=0):
    where, params = _search_params(query, document_id, quality_status, editorial_status, limit, offset, topics=True)
    # Exact total count and stable paging; quality validation remains distinct from default ACCEPTED.
    rows = _run(f"""
        SELECT t.ID_DOCUMENT, d.TITLE AS DOCUMENT_TITLE, t.TOPIC_ID,
               t.TITLE, t.ANGLE, t.EDITORIAL_RATIONALE, t.EVIDENCE_COUNT,
               t.REVIEW_COUNT, t.EDITORIAL_STATUS, t.QUALITY_STATUS,
               t.QUALITY_REASON, t.QUALITY_VALIDATED_AT,
               COUNT(*) OVER() AS TOTAL_COUNT
        FROM `{TOPIC}` t
        JOIN `{DOCUMENT}` d ON d.ID_DOCUMENT = t.ID_DOCUMENT
        {where}
        ORDER BY d.TITLE, t.TITLE, t.ID_DOCUMENT, t.TOPIC_ID
        LIMIT @limit OFFSET @offset
    """, params)
    # Window count is unavailable when OFFSET is beyond the last row; explicit count fallback.
    total = rows[0]["TOTAL_COUNT"] if rows else _run(f"""
        SELECT COUNT(*) AS N FROM `{TOPIC}` t {where}
    """, params)[0]["N"]
    for row in rows:
        row.pop("TOTAL_COUNT", None)
    return {"topics": rows, "total": total, "limit": limit, "offset": offset}


def search_library_units(query=None, document_id=None, limit=50, offset=0):
    where, params = _search_params(query, document_id, None, None, limit, offset, topics=False)
    rows = _run(f"""
        WITH matches AS (
            SELECT u.ID_DOCUMENT, u.UNIT_ID, u.PDF_PAGE, u.FACT, u.QUOTE,
                   u.VERIFICATION_STATUS, u.KIND, u.GEOGRAPHY, u.PERIOD,
                   d.TITLE AS DOCUMENT_TITLE, COUNT(*) OVER() AS TOTAL_COUNT
            FROM `{UNIT}` u
            JOIN `{DOCUMENT}` d ON d.ID_DOCUMENT = u.ID_DOCUMENT
            {where}
            ORDER BY d.TITLE, u.PDF_PAGE, u.UNIT_ID, u.ID_DOCUMENT
            LIMIT @limit OFFSET @offset
        )
        SELECT m.*, (SELECT COUNT(*) FROM `{LINK}` l
                     WHERE l.ID_DOCUMENT = m.ID_DOCUMENT AND l.UNIT_ID = m.UNIT_ID) AS TOPIC_COUNT
        FROM matches m
        ORDER BY m.DOCUMENT_TITLE, m.PDF_PAGE, m.UNIT_ID, m.ID_DOCUMENT
    """, params)
    total = rows[0]["TOTAL_COUNT"] if rows else _run(f"""
        SELECT COUNT(*) AS N FROM `{UNIT}` u {where}
    """, params)[0]["N"]
    for row in rows:
        row.pop("TOTAL_COUNT", None)
    return {"units": rows, "total": total, "limit": limit, "offset": offset}
