"""Persist a local recheck only if the exact saved text is still current."""
import copy
import json
from config import BQ_DATASET, BQ_PROJECT
from utils.bigquery_utils import query_bq

ARTIFACT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_PRODUCTION_ARTIFACT"
WORKSPACE = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_PRODUCTION_WORKFLOW"


def save_revalidation(item, job):
    try:
        query_bq(f"""
            BEGIN TRANSACTION;
            UPDATE `{ARTIFACT}` SET STATUS=@status, RESULT_JSON=PARSE_JSON(@result),
              UPDATED_AT=CURRENT_TIMESTAMP()
            WHERE PRODUCTION_ID=@production_id AND ARTIFACT_ID=@artifact_id
              AND STAGE='DOCUMENT' AND STATUS='validation_failed'
              AND CORPUS_SHA256=@corpus_sha256
              AND JSON_VALUE(RESULT_JSON, '$.text')=@original_text;
            ASSERT @@row_count=1 AS 'SAVED_DOCUMENT_CHANGED';
            IF @completed THEN
              UPDATE `{WORKSPACE}` SET ACTIVE_ARTIFACT_ID=NULL, UPDATED_AT=CURRENT_TIMESTAMP()
              WHERE PRODUCTION_ID=@production_id AND ACTIVE_ARTIFACT_ID=@artifact_id;
            END IF;
            COMMIT TRANSACTION;
        """, {"production_id": item["production_id"], "artifact_id": item["artifact_id"],
              "corpus_sha256": item["corpus_sha256"], "original_text": item["result"]["text"],
              "status": job["status"], "completed": job["status"] == "completed",
              "result": json.dumps(job, ensure_ascii=False, allow_nan=False)})
    except Exception as exc:
        if any(token in str(exc) for token in ("SAVED_DOCUMENT_CHANGED", "concurrent update", "Transaction is aborted", "Could not serialize")):
            from core.production.workflow_service import WorkflowConflict
            raise WorkflowConflict("Le texte sauvegardé a changé pendant sa revalidation ; relire son état.") from exc
        raise
    return {**item, "status": job["status"], "result": copy.deepcopy(job),
            "updated_at": job["validation_check"]["checked_at"]}
