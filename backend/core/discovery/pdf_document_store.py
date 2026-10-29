"""Register original PDF files in private GCS and BigQuery.

Requires PDF_STUDIO_GCS_BUCKET, google-cloud-storage, and the tables in sql/.
"""
import hashlib
import os
import uuid
from datetime import datetime, timezone
from google.cloud import bigquery, storage
from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import get_bigquery_client

TABLE = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOURCE_DOCUMENT"


def register_pdf(data: bytes, filename: str, source_id: str, title: str | None = None) -> dict:
    if not data.startswith(b"%PDF-"):
        raise ValueError("Le fichier ne semble pas être un PDF")
    if not source_id.strip():
        raise ValueError("source_id obligatoire")
    bucket_name = os.getenv("PDF_STUDIO_GCS_BUCKET", "").strip()
    if not bucket_name:
        raise RuntimeError("PDF_STUDIO_GCS_BUCKET non configuré")

    sha = hashlib.sha256(data).hexdigest()
    client = get_bigquery_client()
    rows = list(client.query(
        f"SELECT ID_DOCUMENT, STORAGE_URI, TITLE FROM `{TABLE}` WHERE SHA256=@sha LIMIT 1",
        job_config=bigquery.QueryJobConfig(query_parameters=[
            bigquery.ScalarQueryParameter("sha", "STRING", sha)
        ]),
    ).result())
    if rows:
        r = rows[0]
        return {"id_document": r.ID_DOCUMENT, "sha256": sha,
                "storage_uri": r.STORAGE_URI, "title": r.TITLE, "already_exists": True}

    id_document = str(uuid.uuid4())
    object_name = f"pdf-studio/{sha[:2]}/{sha}.pdf"
    bucket = storage.Client().bucket(bucket_name)
    blob = bucket.blob(object_name)
    # Object is content-addressed: identical PDFs share a single GCS object.
    if not blob.exists():
        blob.upload_from_string(data, content_type="application/pdf", if_generation_match=0)
    uri = f"gs://{bucket_name}/{object_name}"
    params = [
        bigquery.ScalarQueryParameter("id", "STRING", id_document),
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
    return {"id_document": id_document, "sha256": sha, "storage_uri": uri,
            "title": (title or filename).strip(), "already_exists": False}
