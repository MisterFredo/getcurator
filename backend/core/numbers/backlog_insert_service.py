import uuid
from datetime import datetime, timezone
from typing import List

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import get_bigquery_client
from google.cloud import bigquery


TABLE = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS_BACKLOG"


# ============================================================
# HELPERS
# ============================================================

def _now():
    return datetime.now(timezone.utc).isoformat()


def _safe_float(value):

    if value in (None, "", "null"):
        return None

    try:
        return float(value)
    except:
        return None


# ============================================================
# BUILD ROW
# ============================================================

def _build_backlog_row(result: dict):

    output = result.get("output") or {}
    input_data = result.get("input") or {}

    return {
        "ID_BACKLOG": str(uuid.uuid4()),
        "ID_CONTENT": input_data.get("id_content"),

        "RAW_LINE": input_data.get("chiffre"),

        "LABEL": output.get("label"),
        "VALUE": _safe_float(output.get("value")),
        "UNIT": output.get("unit"),

        "ACTOR": output.get("actor"),
        "MARKET": output.get("market"),
        "PERIOD": output.get("period"),

        "CONFIDENCE": output.get("confidence"),

        # 🔥 KEEP / IGNORE recommandé
        "DECISION": output.get("decision"),

        "CREATED_AT": _now(),
    }


# ============================================================
# SINGLE (DEBUG)
# ============================================================

def insert_backlog_result(result: dict):

    row = _build_backlog_row(result)

    client = get_bigquery_client()

    client.load_table_from_json(
        [row],
        TABLE,
        job_config=bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND"
        ),
    ).result()


# ============================================================
# BATCH
# ============================================================

def insert_backlog_batch(results: List[dict]):

    if not results:
        return

    # ============================================================
    # BUILD ROWS
    # ============================================================

    rows = [
        _build_backlog_row(r)
        for r in results
    ]

    # ============================================================
    # DEDUP MEMORY
    # ============================================================

    seen = set()
    deduped_rows = []

    for row in rows:

        key = (
            row.get("ID_CONTENT"),
            row.get("RAW_LINE"),
        )

        if key in seen:
            continue

        seen.add(key)
        deduped_rows.append(row)

    if not deduped_rows:
        return

    # ============================================================
    # INSERT
    # ============================================================

    client = get_bigquery_client()

    client.load_table_from_json(
        deduped_rows,
        TABLE,
        job_config=bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND"
        ),
    ).result()
