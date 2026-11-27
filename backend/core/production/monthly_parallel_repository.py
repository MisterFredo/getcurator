"""Compare-and-swap batch writes in the existing workflow tables."""
import copy
import json
import threading
from config import BQ_DATASET, BQ_PROJECT
from core.production.workflow_service import WorkflowConflict
from utils.bigquery_utils import query_bq

ARTIFACT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_PRODUCTION_ARTIFACT"
WORKSPACE = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_PRODUCTION_WORKFLOW"
_WRITE_LOCK = threading.Lock()


def _write(sql, params):
    # BigQuery may conflict even for different rows in the same partition.
    with _WRITE_LOCK:
        return query_bq(sql, params)


def save_batch(item, job):
    expected = job.get("write_revision", 0)
    saved = {**job, "write_revision": expected + 1}
    active = saved["status"] in {"STARTING", "SUBMISSION_UNKNOWN", "queued", "in_progress"}
    try:
        _write(f"""
            BEGIN TRANSACTION;
            UPDATE `{ARTIFACT}` SET STATUS=@status, RESULT_JSON=PARSE_JSON(@result),
              UPDATED_AT=CURRENT_TIMESTAMP()
            WHERE PRODUCTION_ID=@production_id AND ARTIFACT_ID=@artifact_id
              AND STATUS IN ('STARTING','SUBMISSION_UNKNOWN','queued','in_progress')
              AND COALESCE(SAFE_CAST(JSON_VALUE(RESULT_JSON, '$.write_revision') AS INT64),0)=@revision;
            ASSERT @@row_count=1 AS 'BATCH_STATE_CHANGED';
            IF NOT @active THEN
              UPDATE `{WORKSPACE}` SET ACTIVE_ARTIFACT_ID=NULL, UPDATED_AT=CURRENT_TIMESTAMP()
              WHERE PRODUCTION_ID=@production_id AND ACTIVE_ARTIFACT_ID=@artifact_id;
            END IF;
            COMMIT TRANSACTION;
        """, {"production_id": item["production_id"], "artifact_id": item["artifact_id"],
              "status": saved["status"], "revision": expected, "active": active,
              "result": json.dumps(saved, ensure_ascii=False, allow_nan=False)})
    except Exception as exc:
        if any(token in str(exc) for token in ("BATCH_STATE_CHANGED", "concurrent update", "Transaction is aborted", "Could not serialize")):
            raise WorkflowConflict("Le suivi du lot a évolué ; relire son état avant de poursuivre.") from exc
        raise
    job["write_revision"] = expected + 1
    return {**item, "status": saved["status"], "result": copy.deepcopy(saved), "updated_at": saved["updated_at"]}
