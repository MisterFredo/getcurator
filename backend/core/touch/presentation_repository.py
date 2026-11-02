"""Durable Touch presentation jobs. No inference inside transactions."""
import json
from uuid import UUID
from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq

WORKSPACE = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOUCH_PRESENTATION_WORKFLOW"
ARTIFACT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOUCH_PRESENTATION"
ACTIVE = {"STARTING", "SUBMISSION_UNKNOWN", "queued", "in_progress"}


def initialize_tables():
    query_bq(f"""CREATE TABLE IF NOT EXISTS `{WORKSPACE}` (
      REPORT_ID STRING, NEXT_VERSION INT64, ACTIVE_ARTIFACT_ID STRING, UPDATED_AT TIMESTAMP
    )""")
    query_bq(f"""CREATE TABLE IF NOT EXISTS `{ARTIFACT}` (
      ARTIFACT_ID STRING, REPORT_ID STRING, REPORT_VERSION INT64, VERSION_NUMBER INT64,
      STATUS STRING, RESPONSE_ID STRING, MODEL STRING, SNAPSHOT_SHA256 STRING,
      REQUEST_JSON JSON, RESULT_JSON JSON, CREATED_AT TIMESTAMP, UPDATED_AT TIMESTAMP
    ) CLUSTER BY REPORT_ID""")


def normalize_id(value):
    return str(UUID(str(value)))


def _out(row):
    item = {key.lower(): value for key, value in row.items()}
    for field in ("created_at", "updated_at"):
        if hasattr(item.get(field), "isoformat"):
            item[field] = item[field].isoformat()
    for field in ("request", "result"):
        value = item.pop(field + "_json", None)
        if value is not None:
            item[field] = json.loads(value) if isinstance(value, str) else value
    return item


def get_artifact(report_id, artifact_id):
    rows = query_bq(f"""SELECT * FROM `{ARTIFACT}`
      WHERE REPORT_ID=@id AND ARTIFACT_ID=@artifact LIMIT 2""",
      {"id": report_id, "artifact": normalize_id(artifact_id)}) or []
    if len(rows) > 1:
        raise ValueError("Identifiant de présentation dupliqué.")
    return _out(rows[0]) if rows else None


def list_artifacts(report_id, limit=30, offset=0):
    rows = query_bq(f"""SELECT ARTIFACT_ID, REPORT_ID, REPORT_VERSION, VERSION_NUMBER,
      STATUS, RESPONSE_ID, MODEL, SNAPSHOT_SHA256, CREATED_AT, UPDATED_AT
      FROM `{ARTIFACT}` WHERE REPORT_ID=@id
      ORDER BY VERSION_NUMBER DESC LIMIT @limit OFFSET @offset""",
      {"id": report_id, "limit": min(max(limit, 1), 100), "offset": max(offset, 0)}) or []
    return [_out(row) for row in rows]


def reserve(report_id, artifact_id, report_version, snapshot_hash, snapshot):
    artifact_id = normalize_id(artifact_id)
    existing = get_artifact(report_id, artifact_id)
    if existing:
        if existing["report_version"] != report_version or existing["snapshot_sha256"] != snapshot_hash:
            raise ValueError("Clé de requête déjà utilisée pour une autre version.")
        return existing, False
    query_bq(f"""MERGE `{WORKSPACE}` t USING (SELECT @id REPORT_ID) s
      ON t.REPORT_ID=s.REPORT_ID WHEN NOT MATCHED THEN INSERT
      (REPORT_ID,NEXT_VERSION,ACTIVE_ARTIFACT_ID,UPDATED_AT)
      VALUES(s.REPORT_ID,1,NULL,CURRENT_TIMESTAMP())""", {"id": report_id})
    try:
        query_bq(f"""BEGIN TRANSACTION;
          ASSERT (SELECT COUNT(*) FROM `{WORKSPACE}` WHERE REPORT_ID=@id)=1 AS 'WORKSPACE_DUPLICATE';
          ASSERT NOT EXISTS(SELECT 1 FROM `{ARTIFACT}` WHERE ARTIFACT_ID=@artifact) AS 'REQUEST_ALREADY_RESERVED';
          UPDATE `{WORKSPACE}` SET NEXT_VERSION=NEXT_VERSION+1,
            ACTIVE_ARTIFACT_ID=@artifact, UPDATED_AT=CURRENT_TIMESTAMP()
            WHERE REPORT_ID=@id AND ACTIVE_ARTIFACT_ID IS NULL;
          ASSERT @@row_count=1 AS 'TOUCH_PRESENTATION_BUSY';
          INSERT INTO `{ARTIFACT}` (ARTIFACT_ID,REPORT_ID,REPORT_VERSION,VERSION_NUMBER,
            STATUS,SNAPSHOT_SHA256,REQUEST_JSON,CREATED_AT,UPDATED_AT)
          SELECT @artifact,@id,@version,NEXT_VERSION-1,'STARTING',@hash,
            PARSE_JSON(@snapshot),CURRENT_TIMESTAMP(),CURRENT_TIMESTAMP()
          FROM `{WORKSPACE}` WHERE REPORT_ID=@id;
          COMMIT TRANSACTION;""", {"id": report_id, "artifact": artifact_id,
          "version": report_version, "hash": snapshot_hash,
          "snapshot": json.dumps(snapshot, ensure_ascii=False, allow_nan=False)})
    except Exception as exc:
        existing = get_artifact(report_id, artifact_id)
        if existing and existing["snapshot_sha256"] == snapshot_hash and existing["report_version"] == report_version:
            return existing, False
        if any(token in str(exc) for token in ("BUSY", "DUPLICATE", "RESERVED", "concurrent update", "Could not serialize", "Transaction is aborted")):
            raise PresentationConflict("Une génération est déjà active ou concurrente. Actualisez l’historique.") from exc
        raise
    return get_artifact(report_id, artifact_id), True


class PresentationConflict(Exception):
    pass


def save_job(report_id, artifact_id, job):
    status = job["status"]
    query_bq(f"""BEGIN TRANSACTION;
      UPDATE `{ARTIFACT}` SET STATUS=@status,
        RESPONSE_ID=COALESCE(NULLIF(@response,''),RESPONSE_ID),
        MODEL=COALESCE(NULLIF(@model,''),MODEL), RESULT_JSON=PARSE_JSON(@result),
        UPDATED_AT=CURRENT_TIMESTAMP()
      WHERE REPORT_ID=@id AND ARTIFACT_ID=@artifact
        AND (STATUS IN ('STARTING','SUBMISSION_UNKNOWN','queued','in_progress')
          OR (STATUS='validation_failed' AND @recheck));
      IF @@row_count=1 AND NOT @active THEN
        UPDATE `{WORKSPACE}` SET ACTIVE_ARTIFACT_ID=NULL,UPDATED_AT=CURRENT_TIMESTAMP()
          WHERE REPORT_ID=@id AND ACTIVE_ARTIFACT_ID=@artifact;
      END IF;
      COMMIT TRANSACTION;""", {"id": report_id, "artifact": normalize_id(artifact_id),
      "status": status, "response": job.get("id") or "", "model": job.get("model") or "",
      "result": json.dumps(job, ensure_ascii=False, allow_nan=False),
      "active": status in ACTIVE, "recheck": status not in ACTIVE})
    return get_artifact(report_id, artifact_id)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true", required=True)
    parser.parse_args()
    initialize_tables()
    print("Tables de présentation Touch prêtes.")
