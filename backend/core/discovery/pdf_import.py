"""Import reviewed PDF Studio articles and trace their evidence to the original PDF."""
import os
import uuid
from datetime import datetime, timezone
from google.cloud import bigquery
from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import get_bigquery_client

RAW = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_RAW"
DOC = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOURCE_DOCUMENT"
EVIDENCE = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_DOCUMENT_EVIDENCE"


def import_approved(payload: dict) -> dict:
    document_id = str(payload.get("id_document") or "").strip()
    articles = payload.get("articles")
    if not document_id or not isinstance(articles, list) or not 1 <= len(articles) <= 100:
        raise ValueError("id_document et 1 à 100 articles validés sont requis")
    client = get_bigquery_client()
    doc = list(client.query(
        f"SELECT ID_DOCUMENT, ID_SOURCE, SHA256 FROM `{DOC}` WHERE ID_DOCUMENT=@id LIMIT 1",
        job_config=bigquery.QueryJobConfig(query_parameters=[bigquery.ScalarQueryParameter("id", "STRING", document_id)]),
    ).result())
    if not doc:
        raise ValueError("Document non enregistré")
    doc = doc[0]
    base = os.getenv("PDF_STUDIO_ARTICLE_BASE_URL", "").strip().rstrip("/")
    if not base.startswith("https://"):
        raise ValueError("PDF_STUDIO_ARTICLE_BASE_URL doit être une URL HTTPS de GetCurator")
    seen = set()
    validated = []
    for article in articles:
        if not isinstance(article, dict) or article.get("status") != "DRAFT_REVIEW_REQUIRED":
            raise ValueError("Article non issu du générateur PDF Studio")
        proposal_id = str(article.get("proposal_id") or "").strip()
        if not proposal_id or proposal_id in seen:
            raise ValueError("Identifiant de proposition absent ou répété")
        seen.add(proposal_id)
        if article.get("source_id") != doc.ID_SOURCE or article.get("document_hash") != doc.SHA256:
            raise ValueError("Incohérence entre article, source et PDF enregistré")
        title = str(article.get("title") or "").strip()
        body = str(article.get("body") or "").strip()
        if not title or not body or not str(article.get("excerpt") or "").strip():
            raise ValueError("Titre, extrait et article obligatoires")
        used = article.get("used_unit_ids") or []
        evidence = article.get("evidence") or []
        if not isinstance(used, list) or not isinstance(evidence, list) or len(used) < 1:
            raise ValueError("Preuves documentaires manquantes")
        by_id = {str(e.get("id")): e for e in evidence if isinstance(e, dict) and e.get("id")}
        if any(uid not in by_id for uid in used):
            raise ValueError("Référence à une preuve absente")
        validated.append((proposal_id, title, body, article, used, by_id))

    results = []
    for proposal_id, title, body, article, used, by_id in validated:
        # Deterministic URL provides retry idempotency and the article's canonical source URL.
        stable_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{document_id}:{proposal_id}"))
        url = f"{base}/pdf-source/{stable_id}"
        existing = list(client.query(
            f"SELECT ID_RAW FROM `{RAW}` WHERE SOURCE_URL=@url LIMIT 1",
            job_config=bigquery.QueryJobConfig(query_parameters=[bigquery.ScalarQueryParameter("url", "STRING", url)]),
        ).result())
        if existing:
            results.append({"proposal_id": proposal_id, "id_raw": existing[0].ID_RAW, "source_url": url, "already_exists": True})
            continue
        raw = [{
            "ID_RAW": stable_id,
            "SOURCE_ID": doc.ID_SOURCE,
            "RAW_TEXT": f"{title}\n\n{article['excerpt'].strip()}\n\n{body}",
            "SOURCE_TITLE": title,
            "SOURCE_URL": url,
            "IMPORT_TYPE": "PDF",
            "STATUS": "STORED",
            "CREATED_AT": datetime.now(timezone.utc).isoformat(),
        }]
        evidence_rows = []
        for uid in dict.fromkeys(used):
            ev = by_id[uid]
            page = ev.get("page")
            if page is not None and (isinstance(page, bool) or not isinstance(page, int) or page < 1):
                raise ValueError(f"Numéro de page invalide pour {uid}")
            evidence_rows.append({
                "ID_RAW": stable_id, "ID_DOCUMENT": document_id,
                "ARTICLE_ID": proposal_id, "UNIT_ID": uid,
                "PDF_PAGE": page, "QUOTE": str(ev.get("quote") or ""),
                "FACT": str(ev.get("fact") or ""),
                "VERIFICATION_STATUS": str(ev.get("status") or "NEEDS_REVIEW"),
                "CREATED_AT": datetime.now(timezone.utc).isoformat(),
            })
        # Evidence first: a failure must not create an untraceable article in RAW.
        client.load_table_from_json(evidence_rows, EVIDENCE, job_config=bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")).result()
        client.load_table_from_json(raw, RAW, job_config=bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")).result()
        results.append({"proposal_id": proposal_id, "id_raw": stable_id, "source_url": url, "already_exists": False})
    return {"status": "IMPORTED", "id_document": document_id, "articles": results, "count": len(results)}


def get_pdf_article(id_raw: str) -> dict:
    client = get_bigquery_client()
    params = [bigquery.ScalarQueryParameter("id", "STRING", id_raw)]
    config = bigquery.QueryJobConfig(query_parameters=params)
    rows = list(client.query(f"""
        SELECT r.SOURCE_TITLE, r.RAW_TEXT, r.SOURCE_ID, d.TITLE AS DOCUMENT_TITLE,
               d.STORAGE_URI, d.ID_DOCUMENT
        FROM `{RAW}` r
        JOIN `{EVIDENCE}` e ON e.ID_RAW = r.ID_RAW
        JOIN `{DOC}` d ON d.ID_DOCUMENT = e.ID_DOCUMENT
        WHERE r.ID_RAW=@id AND r.IMPORT_TYPE='PDF'
        LIMIT 1
    """, job_config=config).result())
    if not rows:
        raise ValueError("Article documentaire introuvable")
    r = rows[0]
    evidence = list(client.query(f"""
        SELECT UNIT_ID, PDF_PAGE, QUOTE, FACT, VERIFICATION_STATUS
        FROM `{EVIDENCE}` WHERE ID_RAW=@id ORDER BY PDF_PAGE, UNIT_ID
    """, job_config=config).result())
    # URL is public if the existing media bucket is public; same policy as current media.
    from utils.gcs import BASE_URL, BUCKET_NAME
    prefix = f"gs://{BUCKET_NAME}/"
    pdf_url = f"{BASE_URL.rstrip('/')}/{r.STORAGE_URI[len(prefix):]}" if r.STORAGE_URI.startswith(prefix) else None
    return {"title": r.SOURCE_TITLE, "body": r.RAW_TEXT,
            "document_title": r.DOCUMENT_TITLE, "pdf_url": pdf_url,
            "pages": sorted({e.PDF_PAGE for e in evidence if e.PDF_PAGE is not None}),
            "evidence": [{"unit_id": e.UNIT_ID, "page": e.PDF_PAGE,
                          "quote": e.QUOTE, "fact": e.FACT,
                          "verification_status": e.VERIFICATION_STATUS} for e in evidence]}
