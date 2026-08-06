from datetime import datetime
from typing import Dict, List, Optional
import uuid
from datetime import date
from utils.bigquery_utils import (
    get_bigquery_client,
    query_bq,
    update_bq,
)

from google.cloud import bigquery

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

# ============================================================
# TABLES
# ============================================================

TABLE_CONTENT_RAW = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_RAW"
)

TABLE_COMPANY = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY"
)

# ============================================================
# INSERT RAW ROWS
# ============================================================

def insert_raw_rows(
    rows: List[Dict],
    id_source: str,
    import_type: str = "FILE",
    id_primary_company: Optional[str] = None,
):

    print("[RAW_IMPORT] Début insertion BigQuery")

    client = get_bigquery_client()

    payload = []

    for r in rows:

        payload.append(
            {
                "ID_RAW": str(uuid.uuid4()),

                "CREATED_AT": datetime.utcnow().isoformat(),

                "STATUS": "STORED",

                "ID_PRIMARY_COMPANY": r.get(
                    "ID_PRIMARY_COMPANY",
                    id_primary_company,
                ),

                "SOURCE_TITLE": r["TITLE"],

                "IMPORT_TYPE": import_type,

                "DATE_SOURCE": (
                    r["DATE_SOURCE"].strftime("%Y-%m-%d")
                    if r.get("DATE_SOURCE")
                    else None
                ),

                "RAW_TEXT": r["RAW_TEXT"],

                "SOURCE_ID": id_source,

                "SOURCE_URL": r.get(
                    "SOURCE_URL"
                ),
            }
        )

    print(
        f"[RAW_IMPORT] Nombre de lignes à insérer : {len(payload)}"
    )

    job = client.load_table_from_json(
        payload,
        TABLE_CONTENT_RAW,
        job_config=bigquery.LoadJobConfig(
            source_format=(
                bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
            ),
            write_disposition="WRITE_APPEND",
        ),
    )

    job.result()

    print("[RAW_IMPORT] Insertion BigQuery OK")

    return len(payload)


# ============================================================
# URL EXISTS
# ============================================================

def url_already_exists(
    url: str,
) -> bool:

    client = get_bigquery_client()

    query = f"""
        SELECT 1

        FROM `{TABLE_CONTENT_RAW}`

        WHERE
            SOURCE_URL = @url

        LIMIT 1
    """

    rows = list(
        client.query(
            query,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter(
                        "url",
                        "STRING",
                        url,
                    )
                ]
            ),
        )
    )

    return len(rows) > 0

# ============================================================
# STORE RAW CONTENT
# ============================================================

def store_raw_content(
    source_id: str,
    source_title: str,
    raw_text: str,
    source_url: Optional[str] = None,
    date_source: Optional[date] = None,
    id_primary_company: Optional[str] = None,
):

    return insert_raw_rows(
        rows=[
            {
                "TITLE": source_title,
                "DATE_SOURCE": date_source,
                "RAW_TEXT": raw_text,
                "SOURCE_URL": source_url,
                "ID_PRIMARY_COMPANY": id_primary_company,
            }
        ],
        id_source=source_id,
        import_type="API",
        id_primary_company=id_primary_company,
    )

def list_raw_stock(
    status: Optional[str] = None,
    source_id: Optional[str] = None,
    
    import_type: Optional[str] = None,

    # 🔥 NEW
    id_primary_company: Optional[str] = None,

    limit: int = 50,
    offset: int = 0,
):

    conditions = []
    params = {}

    if status:
        conditions.append("r.STATUS = @status")
        params["status"] = status

    if source_id:
        conditions.append("r.SOURCE_ID = @source_id")
        params["source_id"] = source_id

    if import_type:
        conditions.append("r.IMPORT_TYPE = @import_type")
        params["import_type"] = import_type

    # 🔥 NEW
    if id_primary_company:
        conditions.append(
            "r.ID_PRIMARY_COMPANY = @id_primary_company"
        )
        params["id_primary_company"] = id_primary_company

    where_clause = ""

    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    query = f"""
        SELECT
            r.ID_RAW,

            -- 🔥 NEW
            r.ID_PRIMARY_COMPANY,

            c.NAME AS PRIMARY_COMPANY_NAME,

            r.SOURCE_ID,
            s.NAME AS SOURCE_NAME,

            r.SOURCE_TITLE,
            r.SOURCE_URL,
            r.DATE_SOURCE,

            r.STATUS,
            r.ERROR_MESSAGE,

            r.CREATED_AT,
            r.IMPORT_TYPE,

            COUNT(*) OVER() AS TOTAL_COUNT

        FROM `{TABLE_CONTENT_RAW}` r

        LEFT JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOURCE` s
            ON r.SOURCE_ID = s.SOURCE_ID

        -- 🔥 NEW
        LEFT JOIN `{TABLE_COMPANY}` c
            ON r.ID_PRIMARY_COMPANY = c.ID_COMPANY

        {where_clause}

        ORDER BY r.CREATED_AT DESC

        LIMIT @limit
        OFFSET @offset
    """

    params["limit"] = limit
    params["offset"] = offset

    rows = query_bq(query, params)

    total = rows[0]["TOTAL_COUNT"] if rows else 0

    return {
        "rows": [
            {
                "id_raw": r["ID_RAW"],

                # 🔥 NEW
                "id_primary_company": r.get(
                    "ID_PRIMARY_COMPANY"
                ),

                "primary_company_name": r.get(
                    "PRIMARY_COMPANY_NAME"
                ),

                "source_id": r["SOURCE_ID"],

                "source_name": r.get("SOURCE_NAME"),

                "source_title": r["SOURCE_TITLE"],
                "source_url": r.get("SOURCE_URL"),

                "date_source": r.get("DATE_SOURCE"),

                "status": r["STATUS"],

                "error_message": r.get("ERROR_MESSAGE"),

                "created_at": r["CREATED_AT"],

                "import_type": r.get("IMPORT_TYPE"),
            }
            for r in rows
        ],

        "total": total,
    }

def delete_raw_content(id_raw: str) -> None:

    if not id_raw:
        raise ValueError("id_raw obligatoire")

    query = f"""
        DELETE FROM `{TABLE_CONTENT_RAW}`
        WHERE ID_RAW = @id_raw
    """

    query_bq(
        query,
        {"id_raw": id_raw}
    )

def retry_raw_content(id_raw: str) -> None:

    if not id_raw:
        raise ValueError("id_raw obligatoire")

    # Vérifier que le RAW est bien en ERROR
    check_query = f"""
        SELECT STATUS
        FROM `{TABLE_CONTENT_RAW}`
        WHERE ID_RAW = @id_raw
    """

    rows = query_bq(check_query, {"id_raw": id_raw})

    if not rows:
        raise ValueError("RAW introuvable")

    if rows[0]["STATUS"] != "ERROR":
        raise ValueError("Retry autorisé uniquement pour les ERROR")

    # Reset propre
    update_bq(
        TABLE_CONTENT_RAW,
        {
            "STATUS": "STORED",
            "ERROR_MESSAGE": None,
        },
        where={"ID_RAW": id_raw}
    )

def get_raw_detail(id_raw: str):

    if not id_raw:
        raise ValueError("id_raw obligatoire")

    query = f"""
        SELECT
            r.ID_RAW,

            -- 🔥 NEW
            r.ID_PRIMARY_COMPANY,

            c.NAME AS PRIMARY_COMPANY_NAME,

            r.SOURCE_ID,
            r.SOURCE_TITLE,
            r.SOURCE_URL,

            r.DATE_SOURCE,

            r.RAW_TEXT,

            r.STATUS,
            r.ERROR_MESSAGE,

            r.IMPORT_TYPE,

            r.CREATED_AT

        FROM `{TABLE_CONTENT_RAW}` r

        -- 🔥 NEW
        LEFT JOIN `{TABLE_COMPANY}` c
            ON r.ID_PRIMARY_COMPANY = c.ID_COMPANY

        WHERE r.ID_RAW = @id_raw

        LIMIT 1
    """

    rows = query_bq(query, {"id_raw": id_raw})

    if not rows:
        return None

    r = rows[0]

    return {

        "id_raw": r["ID_RAW"],

        # 🔥 NEW
        "id_primary_company": r.get(
            "ID_PRIMARY_COMPANY"
        ),

        "primary_company_name": r.get(
            "PRIMARY_COMPANY_NAME"
        ),

        "source_id": r["SOURCE_ID"],

        "source_title": r["SOURCE_TITLE"],
        "source_url": r.get("SOURCE_URL"),

        "date_source": r.get("DATE_SOURCE"),

        "raw_text": r.get("RAW_TEXT"),

        "status": r["STATUS"],

        "error_message": r.get("ERROR_MESSAGE"),

        "import_type": r.get("IMPORT_TYPE"),

        "created_at": r["CREATED_AT"],
    }



def update_raw_content(
    id_raw: str,
    date_source: Optional[str],
    source_title: Optional[str],
    source_url: Optional[str] = None,
    raw_text: Optional[str] = None,

    # 🔥 NEW
    id_primary_company: Optional[str] = None,
):

    client = get_bigquery_client()

    table_id = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_RAW"

    query = f"""
        UPDATE `{table_id}`
        SET
            DATE_SOURCE = @date_source,

            SOURCE_TITLE = @source_title,
            SOURCE_URL = @source_url,

            RAW_TEXT = @raw_text,

            -- 🔥 NEW
            ID_PRIMARY_COMPANY = @id_primary_company

        WHERE ID_RAW = @id_raw
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[

            bigquery.ScalarQueryParameter(
                "date_source",
                "DATE",
                date_source
            ),

            bigquery.ScalarQueryParameter(
                "source_title",
                "STRING",
                source_title
            ),

            bigquery.ScalarQueryParameter(
                "source_url",
                "STRING",
                source_url
            ),

            bigquery.ScalarQueryParameter(
                "raw_text",
                "STRING",
                raw_text
            ),

            # 🔥 NEW
            bigquery.ScalarQueryParameter(
                "id_primary_company",
                "STRING",
                id_primary_company
            ),

            bigquery.ScalarQueryParameter(
                "id_raw",
                "STRING",
                id_raw
            ),
        ]
    )

    client.query(
        query,
        job_config=job_config
    ).result()

def get_raw_stats() -> dict:

    query = f"""
        SELECT

            COUNT(*) AS total,

            SUM(
                CASE WHEN STATUS = 'STORED'
                THEN 1 ELSE 0 END
            ) AS total_stored,

            SUM(
                CASE WHEN STATUS = 'PROCESSING'
                THEN 1 ELSE 0 END
            ) AS total_processing,

            SUM(
                CASE WHEN STATUS = 'ERROR'
                THEN 1 ELSE 0 END
            ) AS total_error,

        FROM `{TABLE_CONTENT_RAW}`
    """

    rows = query_bq(query)

    if not rows:
        return {
            "total": 0,
            "total_stored": 0,
            "total_processing": 0,
            "total_error": 0,
        }

    r = rows[0]

    return {

        "total": r.get("total", 0),

        "total_stored": r.get("total_stored", 0),

        "total_processing": r.get("total_processing", 0),

        "total_error": r.get("total_error", 0),

        # 🔥 NEW

    }


