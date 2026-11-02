"""PDF Studio V8 — documentary quality decisions, separate from editorial status."""
import json
from google.cloud import bigquery
from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import get_bigquery_client

TOPIC_TABLE = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_DOCUMENT_TOPIC"


def save_topic_quality(document_id: str, decisions: list[dict]) -> dict:
    if not isinstance(document_id, str) or not document_id.strip():
        raise ValueError("id_document obligatoire.")
    if not isinstance(decisions, list) or not decisions or len(decisions) > 2000:
        raise ValueError("Liste de décisions invalide (1 à 2000).")
    ids = set()
    clean = []
    for decision in decisions:
        if not isinstance(decision, dict):
            raise ValueError("Décision invalide.")
        tid = decision.get("topic_id")
        status = decision.get("quality_status")
        reason = decision.get("quality_reason")
        if not isinstance(tid, str) or not tid.strip() or tid in ids:
            raise ValueError("Identifiant sujet invalide ou dupliqué.")
        if status not in ("ACCEPTED", "REJECTED"):
            raise ValueError(f"Statut qualité invalide pour {tid}.")
        if reason is not None and not isinstance(reason, str):
            raise ValueError(f"Motif invalide pour {tid}.")
        reason = (reason or "").strip()
        if len(reason) > 500:
            raise ValueError(f"Motif trop long pour {tid}.")
        ids.add(tid)
        clean.append({"topic_id": tid.strip(), "quality_status": status, "quality_reason": reason or None})

    client = get_bigquery_client()
    params = [
        bigquery.ScalarQueryParameter("document_id", "STRING", document_id.strip()),
        bigquery.ScalarQueryParameter("decisions_json", "STRING", json.dumps(clean, ensure_ascii=False)),
    ]
    # Reject unknown topics rather than silently losing decisions.
    check_sql = f"""
      SELECT JSON_VALUE(d, "$.topic_id") AS TOPIC_ID
      FROM UNNEST(JSON_QUERY_ARRAY(PARSE_JSON(@decisions_json))) d
      WHERE NOT EXISTS (
        SELECT 1 FROM `{TOPIC_TABLE}` t
        WHERE t.ID_DOCUMENT = @document_id AND t.TOPIC_ID = JSON_VALUE(d, "$.topic_id")
      )
    """
    unknown = list(client.query(check_sql, job_config=bigquery.QueryJobConfig(query_parameters=params)).result())
    if unknown:
        raise ValueError("Sujets absents de la bibliothèque : " + ", ".join(r.TOPIC_ID for r in unknown[:10]))

    # Global validation: require a decision for every topic in the document.
    count_sql = f"SELECT COUNT(*) AS n FROM `{TOPIC_TABLE}` WHERE ID_DOCUMENT = @document_id"
    total = next(iter(client.query(count_sql, job_config=bigquery.QueryJobConfig(query_parameters=params)).result())).n
    if total != len(clean):
        raise ValueError(f"Validation globale incomplète : {len(clean)} sujets transmis pour {total} sujets enregistrés.")

    sql = f"""
      UPDATE `{TOPIC_TABLE}` t
      SET QUALITY_STATUS = JSON_VALUE(d, "$.quality_status"),
          QUALITY_REASON = JSON_VALUE(d, "$.quality_reason"),
          QUALITY_VALIDATED_AT = CURRENT_TIMESTAMP(),
          UPDATED_AT = CURRENT_TIMESTAMP()
      FROM UNNEST(JSON_QUERY_ARRAY(PARSE_JSON(@decisions_json))) d
      WHERE t.ID_DOCUMENT = @document_id AND t.TOPIC_ID = JSON_VALUE(d, "$.topic_id")
    """
    client.query(sql, job_config=bigquery.QueryJobConfig(query_parameters=params)).result()
    return {"status": "SAVED", "id_document": document_id, "updated": len(clean)}
