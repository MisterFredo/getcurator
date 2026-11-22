from config import BQ_DATASET, BQ_PROJECT
from utils.bigquery_utils import query_bq

TABLE = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_DIGEST_SUBJECT"
USERS = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER"


def search_history(query="", audience="", date_from=None, date_to=None, limit=50, offset=0):
    parameters = {
        "query": query.strip().casefold(), "audience": audience,
        "date_from": date_from.isoformat() if date_from else "",
        "date_to": date_to.isoformat() if date_to else "",
        "limit": limit, "offset": offset,
    }
    filtered = f"""
        WITH users AS (
          SELECT ID_USER, MAX(TO_JSON_STRING(u)) AS metadata
          FROM `{USERS}` u GROUP BY ID_USER
        ), documents AS (
          SELECT d.ID AS id, d.USER_ID AS user_id,
                 COALESCE(NULLIF(JSON_VALUE(d.DOCUMENT_JSON, '$.profile.name'), ''),
                          JSON_VALUE(u.metadata, '$.DISPLAY_NAME'),
                          JSON_VALUE(u.metadata, '$.NAME'), d.USER_ID) AS name,
                 COALESCE(JSON_VALUE(d.DOCUMENT_JSON, '$.profile.company'),
                          JSON_VALUE(u.metadata, '$.COMPANY'), '') AS company,
                 COALESCE(JSON_VALUE(u.metadata, '$.EMAIL'), '') AS email,
                 CASE WHEN UPPER(JSON_VALUE(u.metadata, '$.PROFILE_TYPE')) = 'EXPERT'
                      THEN 'expert' ELSE 'user' END AS audience,
                 d.PERIOD_START AS period_start, d.PERIOD_END AS end_exclusive,
                 d.GENERATED_AT AS generated_at
          FROM `{TABLE}` d LEFT JOIN users u ON u.ID_USER = d.USER_ID
        ), filtered AS (
          SELECT * FROM documents
          WHERE (@query = '' OR STRPOS(LOWER(CONCAT(name, ' ', company, ' ', email, ' ', user_id)), @query) > 0)
            AND (@audience = '' OR audience = @audience)
            AND (@date_from = '' OR end_exclusive > SAFE_CAST(@date_from AS DATE))
            AND (@date_to = '' OR period_start <= SAFE_CAST(@date_to AS DATE))
        )
    """
    counts = query_bq(sql=filtered + " SELECT COUNT(*) AS total FROM filtered", params=parameters) or []
    rows = query_bq(sql=filtered + """
        SELECT id, user_id, name, company, email, audience,
               CAST(period_start AS STRING) AS period_start,
               CAST(DATE_SUB(end_exclusive, INTERVAL 1 DAY) AS STRING) AS period_end,
               CAST(generated_at AS STRING) AS generated_at
        FROM filtered
        ORDER BY period_start DESC, generated_at DESC, id
        LIMIT @limit OFFSET @offset
    """, params=parameters) or []
    return {"digests": rows, "total": int(counts[0]["total"]) if counts else 0}
