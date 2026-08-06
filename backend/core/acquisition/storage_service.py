from datetime import datetime
from typing import Dict, List, Optional
import uuid

from google.cloud import bigquery

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    get_bigquery_client,
)

# ============================================================
# TABLES
# ============================================================

TABLE_CONTENT_RAW = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_RAW"
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

    # 🔥 NEW
    id_primary_company: Optional[str] = None,
) -> str:

    if not source_id:
        raise ValueError("source_id obligatoire")

    if not source_title or not source_title.strip():
        raise ValueError("source_title obligatoire")

    if not raw_text or not raw_text.strip():
        raise ValueError("raw_text vide")

    raw_id = str(uuid.uuid4())

    now_iso = datetime.utcnow().isoformat()

    row = [{

        "ID_RAW": raw_id,

        # 🔥 NEW
        "ID_PRIMARY_COMPANY": id_primary_company,

        "SOURCE_ID": source_id,

        "SOURCE_TITLE": source_title.strip(),
        "SOURCE_URL": source_url,

        "RAW_TEXT": raw_text.strip(),

        "DATE_SOURCE": (
            date_source.isoformat()
            if date_source
            else None
        ),

        "STATUS": "STORED",

        "CREATED_AT": now_iso,

        "PROCESSED_AT": None,

        "GENERATED_CONTENT_ID": None,

        "ERROR_MESSAGE": None,
    }]

    client = get_bigquery_client()

    client.load_table_from_json(
        row,
        TABLE_CONTENT_RAW,
        job_config=bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND"
        ),
    ).result()

    return raw_id
