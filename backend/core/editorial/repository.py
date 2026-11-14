import json

from config import BQ_DATASET, BQ_PROJECT
from utils.bigquery_utils import query_bq

PREFIX = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_EDITORIAL"
LOCK = f"{PREFIX}_LOCK"
JOB = f"{PREFIX}_JOB"
EDITION = f"{PREFIX}_EDITION"
SOURCE_UNIVERSE = f"{PREFIX}_SOURCE_UNIVERSE"
CONTENT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_ENRICHED"
ACTIVE = {"pending", "starting", "queued", "in_progress", "submission_unknown"}
SUMMARY = """
EDITION_ID, JOB_ID, CAST(EDITION_DATE AS STRING) AS DATE, UNIVERSE_ID,
UNIVERSE_LABEL, CONTENT_COUNT, STATUS, RESPONSE_ID, ERROR
"""


def load_contents(day):
    return query_bq(f"""
        SELECT c.id_content, c.title, c.excerpt, c.source_url, c.source_title,
          c.signal_analytique, CAST(c.published_at AS STRING) AS published_at,
          s.universe_id, s.universe_label
        FROM `{CONTENT}` c
        LEFT JOIN `{SOURCE_UNIVERSE}` s
          ON s.source_id = CAST(c.source_id AS STRING)
        WHERE c.status = 'PUBLISHED' AND c.is_active IS TRUE
          AND c.created_at >= TIMESTAMP(DATE(@day), 'Europe/Paris')
          AND c.created_at < TIMESTAMP(DATE_ADD(DATE(@day), INTERVAL 1 DAY), 'Europe/Paris')
        ORDER BY c.created_at, c.id_content, s.universe_id
    """, {"day": day}) or []


def job_header(job_id):
    rows = query_bq(f"""
        SELECT JOB_ID, CAST(EDITION_DATE AS STRING) AS DATE
        FROM `{JOB}` WHERE JOB_ID=@id
    """, {"id": job_id}) or []
    return {key.lower(): value for key, value in rows[0].items()} if rows else None


def reserve(job_id, day, editions):
    query_bq(f"""
        BEGIN TRANSACTION;
        UPDATE `{LOCK}` SET UPDATED_AT=CURRENT_TIMESTAMP() WHERE LOCK_ID='DAILY';
        ASSERT @@row_count=1 AS 'EDITORIAL_LOCK_INVALID';
        IF NOT EXISTS (SELECT 1 FROM `{JOB}` WHERE JOB_ID=@id) THEN
          ASSERT NOT EXISTS (
            SELECT 1 FROM `{EDITION}`
            WHERE EDITION_DATE=DATE(@day)
              AND STATUS IN ('pending','starting','queued','in_progress','submission_unknown')
          ) AS 'EDITORIAL_BUSY';
          INSERT INTO `{JOB}` VALUES (@id, DATE(@day), CURRENT_TIMESTAMP());
          INSERT INTO `{EDITION}`
            (EDITION_ID, JOB_ID, EDITION_DATE, UNIVERSE_ID, UNIVERSE_LABEL,
             CONTENT_COUNT, STATUS, CONTENTS_JSON, CREATED_AT, UPDATED_AT)
          SELECT JSON_VALUE(item, '$.edition_id'), @id, DATE(@day),
            JSON_VALUE(item, '$.universe_id'), JSON_VALUE(item, '$.universe_label'),
            ARRAY_LENGTH(JSON_QUERY_ARRAY(item, '$.contents')), 'pending',
            JSON_QUERY(item, '$.contents'), CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()
          FROM UNNEST(JSON_QUERY_ARRAY(PARSE_JSON(@editions))) AS item;
        END IF;
        COMMIT TRANSACTION;
    """, {"id": job_id, "day": day, "editions": json.dumps(editions, ensure_ascii=False)})


def _rows(sql, params):
    rows = query_bq(sql, params) or []
    return [{key.lower(): value for key, value in row.items()} for row in rows]


def list_job_editions(job_id):
    return _rows(f"""
        SELECT {SUMMARY} FROM `{EDITION}` WHERE JOB_ID=@id ORDER BY UNIVERSE_LABEL, UNIVERSE_ID
    """, {"id": job_id})


def list_editions(day, universe, limit, offset):
    return _rows(f"""
        SELECT {SUMMARY}
        FROM `{EDITION}`
        WHERE STATUS='completed'
          AND (@day='' OR EDITION_DATE=SAFE_CAST(@day AS DATE))
          AND (@universe='' OR UNIVERSE_ID=@universe)
        QUALIFY ROW_NUMBER() OVER (
          PARTITION BY EDITION_DATE, UNIVERSE_ID ORDER BY CREATED_AT DESC, EDITION_ID DESC
        )=1
        ORDER BY EDITION_DATE DESC, UNIVERSE_LABEL, UNIVERSE_ID LIMIT @limit OFFSET @offset
    """, {"day": day or "", "universe": universe or "", "limit": limit, "offset": offset})


def read_edition(edition_id):
    rows = _rows(f"""
        SELECT {SUMMARY}, TO_JSON_STRING(CONTENTS_JSON) AS CONTENTS,
          TO_JSON_STRING(RESULT_JSON) AS RESULT
        FROM `{EDITION}` WHERE EDITION_ID=@id
    """, {"id": edition_id})
    if not rows:
        return None
    edition = rows[0]
    edition["contents"] = json.loads(edition["contents"])
    edition["result"] = json.loads(edition["result"]) if edition["result"] else None
    return edition


def claim(edition_id, claim_id):
    # Use a unique claim token until the provider response ID replaces it.
    query_bq(f"""
        UPDATE `{EDITION}` SET STATUS='starting', RESPONSE_ID=@claim,
          UPDATED_AT=CURRENT_TIMESTAMP()
        WHERE EDITION_ID=@id AND STATUS='pending'
    """, {"id": edition_id, "claim": claim_id})
    row = read_edition(edition_id)
    return row if row and row["status"] == "starting" and row["response_id"] == claim_id else None


def save(edition_id, expected_id, status, *, response_id="", result=None, error=""):
    query_bq(f"""
        UPDATE `{EDITION}` SET STATUS=@status,
          RESPONSE_ID=COALESCE(NULLIF(@response_id,''), RESPONSE_ID),
          RESULT_JSON=PARSE_JSON(@result), ERROR=NULLIF(@error,''),
          UPDATED_AT=CURRENT_TIMESTAMP()
        WHERE EDITION_ID=@id AND RESPONSE_ID=@expected
          AND STATUS IN ('starting','queued','in_progress','submission_unknown')
          AND NOT (STATUS='in_progress' AND @status='queued')
    """, {"id": edition_id, "expected": expected_id, "status": status,
          "response_id": response_id, "result": json.dumps(result, ensure_ascii=False),
          "error": error})
