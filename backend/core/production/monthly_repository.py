"""Monthly metadata lives in the existing frozen Production corpus JSON."""
from config import BQ_DATASET, BQ_PROJECT
from core.production.repository import get_production
from core.production.workflow_repository import summaries, get_artifact
from utils.bigquery_utils import query_bq

TABLE = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_PRODUCTION"
ARTIFACT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_PRODUCTION_ARTIFACT"


def list_monthlies(user_id="", month="", status="", limit=50, offset=0):
    rows = query_bq(f"""
        WITH latest AS (
          SELECT PRODUCTION_ID, STAGE, STATUS AS ARTIFACT_STATUS,
                 JSON_VALUE(RESULT_JSON, '$.review.passed') AS REVIEW_PASSED
          FROM `{ARTIFACT}`
          QUALIFY ROW_NUMBER() OVER (PARTITION BY PRODUCTION_ID ORDER BY VERSION_NUMBER DESC)=1
        ), entries AS (
          SELECT p.PRODUCTION_ID, p.TITLE, p.CREATED_AT, p.OUTPUT_LANGUAGE,
            JSON_VALUE(p.CORPUS_JSON, '$.request.monthly_user.user_id') AS USER_ID,
            JSON_VALUE(p.CORPUS_JSON, '$.request.monthly_user.name') AS NAME,
            JSON_VALUE(p.CORPUS_JSON, '$.request.monthly_user.month') AS MONTH,
            JSON_VALUE(p.CORPUS_JSON, '$.request.monthly_user.provisional') AS PROVISIONAL,
            CASE
              WHEN l.STAGE IN ('REVIEW','REVIEW_BATCH') AND l.ARTIFACT_STATUS='completed' AND l.REVIEW_PASSED='true' THEN 'completed'
              WHEN l.ARTIFACT_STATUS='SUBMISSION_UNKNOWN' THEN 'submission_unknown'
              WHEN l.ARTIFACT_STATUS IN ('failed','incomplete','cancelled','validation_failed') THEN 'needs_attention'
              WHEN l.STAGE IN ('REVIEW','REVIEW_BATCH') AND l.ARTIFACT_STATUS='completed' AND l.REVIEW_PASSED='false' THEN 'needs_attention'
              WHEN l.STAGE IN ('REVIEW_PAGE','REVIEW_CROSS') THEN 'reviewing'
              WHEN l.STAGE IN ('REVIEW','REVIEW_BATCH') THEN 'reviewing'
              WHEN l.STAGE='DOCUMENT' THEN 'writing'
              WHEN l.STAGE='APPROVED_PLAN' THEN 'writing'
              WHEN l.STAGE='PLAN' THEN 'planning'
              ELSE 'prepared' END AS MONTHLY_STATUS
          FROM `{TABLE}` p LEFT JOIN latest l USING(PRODUCTION_ID)
          WHERE JSON_VALUE(p.CORPUS_JSON, '$.request.monthly_user.kind')='MONTHLY_USER'
        )
        SELECT * FROM entries
        WHERE (@user='' OR USER_ID=@user) AND (@month='' OR MONTH=@month)
          AND (@status='' OR MONTHLY_STATUS=@status)
        ORDER BY CREATED_AT DESC, PRODUCTION_ID DESC LIMIT @limit OFFSET @offset
    """, {"user": user_id, "month": month, "status": status,
            "limit": min(max(limit, 1), 100), "offset": max(offset, 0)}) or []
    return [{
        "production_id": r["PRODUCTION_ID"], "title": r["TITLE"],
        "created_at": r["CREATED_AT"].isoformat() if hasattr(r["CREATED_AT"], "isoformat") else str(r["CREATED_AT"]),
        "language": r["OUTPUT_LANGUAGE"], "user_id": r["USER_ID"], "name": r["NAME"],
        "month": r["MONTH"], "provisional": r["PROVISIONAL"] == "true", "status": r["MONTHLY_STATUS"],
    } for r in rows]


def latest_for(user_id, month, language):
    rows = query_bq(f"""
        SELECT PRODUCTION_ID FROM `{TABLE}`
        WHERE JSON_VALUE(CORPUS_JSON, '$.request.monthly_user.kind')='MONTHLY_USER'
          AND JSON_VALUE(CORPUS_JSON, '$.request.monthly_user.user_id')=@user
          AND JSON_VALUE(CORPUS_JSON, '$.request.monthly_user.month')=@month
          AND OUTPUT_LANGUAGE=@language
        ORDER BY CREATED_AT DESC, PRODUCTION_ID DESC LIMIT 1
    """, {"user": user_id, "month": month, "language": language}) or []
    return get_production(rows[0]["PRODUCTION_ID"]) if rows else None


def previous_reference(user_id, month, language):
    rows = query_bq(f"""
        SELECT p.PRODUCTION_ID, a.ARTIFACT_ID,
               JSON_VALUE(a.REQUEST_JSON, '$.document_artifact_id') AS DOCUMENT_ARTIFACT_ID
        FROM `{TABLE}` p JOIN `{ARTIFACT}` a USING(PRODUCTION_ID)
        WHERE JSON_VALUE(p.CORPUS_JSON, '$.request.monthly_user.kind')='MONTHLY_USER'
          AND JSON_VALUE(p.CORPUS_JSON, '$.request.monthly_user.user_id')=@user
          AND JSON_VALUE(p.CORPUS_JSON, '$.request.monthly_user.month')=@month
          AND p.OUTPUT_LANGUAGE=@language
          AND a.STAGE IN ('REVIEW','REVIEW_BATCH') AND a.STATUS='completed'
          AND JSON_VALUE(a.RESULT_JSON, '$.review.passed')='true'
          AND JSON_VALUE(p.CORPUS_JSON, '$.request.monthly_user.provisional')='false'
        ORDER BY p.CREATED_AT DESC, a.VERSION_NUMBER DESC LIMIT 1
    """, {"user": user_id, "month": month, "language": language}) or []
    if not rows:
        return None
    row = rows[0]
    production = get_production(row["PRODUCTION_ID"])
    document = get_artifact(row["PRODUCTION_ID"], row["DOCUMENT_ARTIFACT_ID"])
    if not production or not document or document["status"] != "completed":
        return None
    return production, document
