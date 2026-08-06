import re
import uuid
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, date
from typing import Optional, Dict, Any, List
from utils.bigquery_utils import get_bigquery_client
from google.cloud import bigquery
from config import BQ_PROJECT, BQ_DATASET


# ============================================================
# CONFIG
# ============================================================

TABLE = "RATECARD_CONTENT_RAW"


# ============================================================
# INSERT BIGQUERY
# ============================================================

def insert_raw_rows(
    rows: List[Dict],
    id_source: str,
    import_type: str = "FILE",

    # 🔥 NEW
    id_primary_company: Optional[str] = None,
):

    print("[RAW_IMPORT] Début insertion BigQuery")

    client = get_bigquery_client()

    table_id = f"{BQ_PROJECT}.{BQ_DATASET}.{TABLE}"

    payload = []

    for r in rows:

        payload.append(
            {
                "ID_RAW": str(uuid.uuid4()),

                "CREATED_AT": datetime.utcnow().isoformat(),

                "STATUS": "STORED",

                # 🔥 NEW
                "ID_PRIMARY_COMPANY": r.get(
                    "ID_PRIMARY_COMPANY",
                    id_primary_company
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

                # 🔥 IMPORTANT
                "SOURCE_URL": r.get("SOURCE_URL"),
            }
        )

    print(f"[RAW_IMPORT] Nombre de lignes à insérer : {len(payload)}")

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition="WRITE_APPEND",
    )

    job = client.load_table_from_json(
        payload,
        table_id,
        job_config=job_config,
    )

    job.result()

    print("[RAW_IMPORT] Insertion BigQuery OK")

    return len(payload)
