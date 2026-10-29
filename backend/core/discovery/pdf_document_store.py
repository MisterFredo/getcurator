"""PDF Studio document registry using the existing GCS media client and bucket."""
import hashlib
import uuid
from google.cloud import bigquery
from google.api_core.exceptions import PreconditionFailed
from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import get_bigquery_client
from utils.gcs import bucket, BUCKET_NAME, BASE_URL

TABLE = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOURCE_DOCUMENT"


def register_pdf(data: bytes, filename: str, source_id: str, title: str | None = None) -> dict:
    if not data.startswith(b"%PDF-"):
        raise ValueError("Fichier PDF invalide")
    if not source_id or not source_id.strip():
        raise ValueError("source_id obligatoire")
    sha = hashlib.sha256(data).hexdigest()
    client = get_bigquery_client()
    params = [bigquery.ScalarQueryParameter("sha", "STRING", sha)]
    rows = list(client.query(
        f"SELECT ID_DOCUMENT, STORAGE_URI, TITLE FROM `{TABLE}` WHERE SHA256=@sha LIMIT 1",
        job_config=bigquery.QueryJobConfig(query_parameters=params),
    ).result())
    if rows:
        row = rows[0]
        return {"id_document": row.ID_DOCUMENT, "sha256": sha, "storage_uri": row.STORAGE_URI,
                "title": row.TITLE, "already_exists": True}
    path = f"pdf-studio/documents/{sha}.pdf"
    blob = bucket.blob(path)
    try:
        blob.upload_from_string(data, content_type="application/pdf", if_generation_match=0)
    except PreconditionFailed:
        pass  # Concurrent upload of identical bytes.
    document_id = str(uuid.uuid4())
    uri = f"gs://{BUCKET_NAME}/{path}"
    params = [
        bigquery.ScalarQueryParameter("id", "STRING", document_id),
        bigquery.ScalarQueryParameter("source", "STRING", source_id),
        bigquery.ScalarQueryParameter("title", "STRING", (title or filename).strip()),
        bigquery.ScalarQueryParameter("filename", "STRING", filename),
        bigquery.ScalarQueryParameter("sha", "STRING", sha),
        bigquery.ScalarQueryParameter("uri", "STRING", uri),
        bigquery.ScalarQueryParameter("bytes", "INT64", len(data)),
    ]
    client.query(f"""
        INSERT INTO `{TABLE}`
        (ID_DOCUMENT, ID_SOURCE, TITLE, ORIGINAL_FILENAME, SHA256, STORAGE_URI, FILE_SIZE_BYTES, CREATED_AT)
        VALUES (@id, @source, @title, @filename, @sha, @uri, @bytes, CURRENT_TIMESTAMP())
    """, job_config=bigquery.QueryJobConfig(query_parameters=params)).result()
    return {"id_document": document_id, "sha256": sha, "storage_uri": uri,
            "title": (title or filename).strip(), "already_exists": False}
