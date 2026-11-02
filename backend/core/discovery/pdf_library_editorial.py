"""Editorial qualification of documentary topics. Never creates RAW content."""
from google.cloud import bigquery
from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import get_bigquery_client

TOPIC = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_DOCUMENT_TOPIC"
ALLOWED = {"REVIEW", "SELECTED", "IGNORED"}


def update_topic_editorial_status(document_id: str, topic_id: str, status: str) -> dict:
    if not document_id or not document_id.strip() or not topic_id or not topic_id.strip():
        raise ValueError("Document et sujet obligatoires.")
    if status not in ALLOWED:
        raise ValueError("Statut éditorial invalide.")
    client = get_bigquery_client()
    params = [
        bigquery.ScalarQueryParameter("document_id", "STRING", document_id),
        bigquery.ScalarQueryParameter("topic_id", "STRING", topic_id),
        bigquery.ScalarQueryParameter("status", "STRING", status),
    ]
    config = bigquery.QueryJobConfig(query_parameters=params)
    # Atomic guard: quality must have been validated and accepted for selection.
    sql = f"""
        UPDATE `{TOPIC}`
        SET EDITORIAL_STATUS = @status, UPDATED_AT = CURRENT_TIMESTAMP()
        WHERE ID_DOCUMENT = @document_id AND TOPIC_ID = @topic_id
          AND (@status != 'SELECTED' OR
               (QUALITY_VALIDATED_AT IS NOT NULL AND QUALITY_STATUS = 'ACCEPTED'))
    """
    job = client.query(sql, job_config=config)
    job.result()
    if job.num_dml_affected_rows == 1:
        return {"id_document": document_id, "topic_id": topic_id, "editorial_status": status}
    # Explain failed update without confusing missing topic with unvalidated quality.
    check = list(client.query(f"""
        SELECT QUALITY_STATUS, QUALITY_VALIDATED_AT, EDITORIAL_STATUS
        FROM `{TOPIC}` WHERE ID_DOCUMENT = @document_id AND TOPIC_ID = @topic_id
        LIMIT 2
    """, job_config=config).result())
    if not check:
        raise LookupError("Sujet introuvable.")
    if len(check) > 1:
        raise ValueError("Plusieurs sujets correspondent à cet identifiant.")
    raise ValueError("Pour sélectionner un sujet, son contrôle qualité doit être validé et accepté.")
