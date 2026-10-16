"""Durable artifacts and a transactional per-production generation lock.

No API calls in transactions. Artifact IDs are client-generated UUIDs used as
idempotency keys. BigQuery transaction conflicts fail closed; no blind retries.
"""
import json
from uuid import UUID
from config import BQ_DATASET, BQ_PROJECT
from utils.bigquery_utils import query_bq

WORKSPACE = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_PRODUCTION_WORKFLOW"
ARTIFACT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_PRODUCTION_ARTIFACT"
ACTIVE = {"STARTING", "SUBMISSION_UNKNOWN", "queued", "in_progress"}


def normalize_id(value):
    return str(UUID(value))


def _json(value):
    return json.loads(value) if isinstance(value, str) else value


def _out(row, detail=True):
    result = {key.lower(): value for key, value in row.items()}
    for key in ("created_at", "updated_at"):
        value = result.get(key)
        result[key] = value.isoformat() if hasattr(value, "isoformat") else value
    if detail:
        result["request"] = _json(result.pop("request_json", None))
        result["result"] = _json(result.pop("result_json", None))
    return result


def get_artifact(production_id, artifact_id):
    rows = query_bq(f"""
        SELECT * FROM `{ARTIFACT}`
        WHERE PRODUCTION_ID=@production_id AND ARTIFACT_ID=@artifact_id LIMIT 2
    """, {"production_id": production_id, "artifact_id": normalize_id(artifact_id)}) or []
    if len(rows) > 1:
        raise ValueError("Plusieurs versions partagent le même identifiant.")
    return _out(rows[0]) if rows else None


def list_artifacts(production_id, limit=30, offset=0):
    rows = query_bq(f"""
        SELECT ARTIFACT_ID, PRODUCTION_ID, VERSION_NUMBER, STAGE, STATUS,
               RESPONSE_ID, MODEL, CORPUS_SHA256, PARENT_ARTIFACT_ID,
               CREATED_AT, UPDATED_AT
        FROM `{ARTIFACT}` WHERE PRODUCTION_ID=@production_id
        ORDER BY VERSION_NUMBER DESC LIMIT @limit OFFSET @offset
    """, {"production_id": production_id, "limit": min(max(limit, 1), 100),
          "offset": max(offset, 0)}) or []
    return [_out(row, detail=False) for row in rows]


def ensure_workspace(production_id):
    query_bq(f"""
        MERGE `{WORKSPACE}` t USING (SELECT @id PRODUCTION_ID) s
        ON t.PRODUCTION_ID=s.PRODUCTION_ID
        WHEN NOT MATCHED THEN INSERT
          (PRODUCTION_ID, NEXT_VERSION, ACTIVE_ARTIFACT_ID, UPDATED_AT)
          VALUES (s.PRODUCTION_ID, 1, NULL, CURRENT_TIMESTAMP())
    """, {"id": production_id})


def reserve_artifact(production_id, artifact_id, stage, corpus_sha256,
                     request, parent_id=None, ready_result=None):
    artifact_id = normalize_id(artifact_id)
    existing = get_artifact(production_id, artifact_id)
    if existing:
        if (existing["stage"] != stage or existing["request"] != request
                or existing["parent_artifact_id"] != parent_id
                or existing["corpus_sha256"] != corpus_sha256):
            raise ValueError("Cette clé de requête désigne déjà une autre opération.")
        return existing, False
    ensure_workspace(production_id)
    # All writers update this row: concurrent transactions cannot both commit.
    query_bq(f"""
        BEGIN TRANSACTION;
        ASSERT (SELECT COUNT(*) FROM `{WORKSPACE}` WHERE PRODUCTION_ID=@id)=1
          AS 'WORKSPACE_DUPLICATE';
        ASSERT NOT EXISTS(SELECT 1 FROM `{ARTIFACT}` WHERE ARTIFACT_ID=@artifact_id)
          AS 'REQUEST_ALREADY_RESERVED';
        UPDATE `{WORKSPACE}` SET NEXT_VERSION=NEXT_VERSION+1,
          ACTIVE_ARTIFACT_ID=IF(@ready, NULL, @artifact_id), UPDATED_AT=CURRENT_TIMESTAMP()
        WHERE PRODUCTION_ID=@id AND ACTIVE_ARTIFACT_ID IS NULL;
        ASSERT @@row_count=1 AS 'PRODUCTION_BUSY';
        INSERT INTO `{ARTIFACT}`
          (ARTIFACT_ID, PRODUCTION_ID, VERSION_NUMBER, STAGE, STATUS, CORPUS_SHA256,
           PARENT_ARTIFACT_ID, REQUEST_JSON, RESULT_JSON, CREATED_AT, UPDATED_AT)
        SELECT @artifact_id, @id, NEXT_VERSION-1, @stage,
          IF(@ready, 'completed', 'STARTING'), @hash,
          NULLIF(@parent, ''), PARSE_JSON(@request), PARSE_JSON(@result),
          CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()
        FROM `{WORKSPACE}` WHERE PRODUCTION_ID=@id;
        COMMIT TRANSACTION;
    """, {"id": production_id, "artifact_id": artifact_id, "stage": stage,
          "hash": corpus_sha256, "parent": parent_id or "",
          "request": json.dumps(request, ensure_ascii=False, allow_nan=False),
          "result": json.dumps(ready_result, ensure_ascii=False, allow_nan=False),
          "ready": ready_result is not None})
    return get_artifact(production_id, artifact_id), True


def save_job(production_id, artifact_id, job):
    """Persist the result and release the lock in one transaction.

    Terminal results cannot be overwritten by a slower nonterminal poll.
    Validation failures may be rechecked after a validator correction.
    """
    status = job["status"]
    query_bq(f"""
        BEGIN TRANSACTION;
        UPDATE `{ARTIFACT}` SET STATUS=@status,
          RESPONSE_ID=COALESCE(NULLIF(@response_id, ''), RESPONSE_ID),
          MODEL=COALESCE(NULLIF(@model, ''), MODEL), RESULT_JSON=PARSE_JSON(@result),
          UPDATED_AT=CURRENT_TIMESTAMP()
        WHERE PRODUCTION_ID=@id AND ARTIFACT_ID=@artifact_id
          AND (STATUS IN ('STARTING','SUBMISSION_UNKNOWN','queued','in_progress')
               OR (STATUS='validation_failed' AND @recheck));
        IF @@row_count=1 AND NOT @active THEN
          UPDATE `{WORKSPACE}` SET ACTIVE_ARTIFACT_ID=NULL, UPDATED_AT=CURRENT_TIMESTAMP()
          WHERE PRODUCTION_ID=@id AND ACTIVE_ARTIFACT_ID=@artifact_id;
        END IF;
        COMMIT TRANSACTION;
    """, {"id": production_id, "artifact_id": normalize_id(artifact_id),
          "status": status, "response_id": job.get("id") or "",
          "model": job.get("model") or "",
          "result": json.dumps(job, ensure_ascii=False, allow_nan=False),
          "active": status in ACTIVE, "recheck": status not in ACTIVE})
    return get_artifact(production_id, artifact_id)


def summaries(production_ids):
    if not production_ids:
        return {}
    params = {f"p{i}": value for i, value in enumerate(production_ids)}
    placeholders = ",".join(f"@{key}" for key in params)
    rows = query_bq(f"""
        SELECT PRODUCTION_ID, COUNT(*) ARTIFACT_COUNT,
          COUNTIF(STAGE='DOCUMENT' AND STATUS='completed') DOCUMENT_COUNT,
          MAX(UPDATED_AT) WORKFLOW_UPDATED_AT,
          ARRAY_AGG(STRUCT(ARTIFACT_ID, STAGE, STATUS, VERSION_NUMBER)
                    ORDER BY VERSION_NUMBER DESC LIMIT 1)[OFFSET(0)] LATEST
        FROM `{ARTIFACT}` WHERE PRODUCTION_ID IN ({placeholders}) GROUP BY PRODUCTION_ID
    """, params) or []
    result = {}
    for row in rows:
        value = row["WORKFLOW_UPDATED_AT"]
        result[row["PRODUCTION_ID"]] = {
            "artifact_count": row["ARTIFACT_COUNT"], "document_count": row["DOCUMENT_COUNT"],
            "updated_at": value.isoformat() if hasattr(value, "isoformat") else value,
            "latest": dict(row["LATEST"]),
        }
    return result
