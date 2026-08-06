import re
import uuid
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, date
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin

from google.cloud import bigquery

from config import BQ_PROJECT, BQ_DATASET
from api.content.models import ContentCreate, ContentUpdate
from core.content.ai import generate_summary
from core.content.news_ai import generate_news
from utils.bigquery_utils import (
    query_bq,
    insert_bq,
    update_bq,
    get_bigquery_client,
)

from core.numbers.service import get_numbers_from_content
from core.numbers.backlog_llm import process_backlog_row
from core.numbers.backlog_insert_service import insert_backlog_batch
from core.content.publish_sync_service import (
    after_publish_sync,
)

# ============================================================
# TABLE
# ============================================================

TABLE_CONTENT = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"
)


# ============================================================
# TABLES
# ============================================================

TABLE_CONTENT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"

TABLE_CONTENT_TOPIC = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_TOPIC"
TABLE_CONTENT_COMPANY = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_COMPANY"

TABLE_CONTENT_CONCEPT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_CONCEPT"
TABLE_CONTENT_SOLUTION = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_SOLUTION"
TABLE_CONTENT_RAW = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_RAW"

TABLE_TOPIC = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOPIC"
TABLE_COMPANY = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY"
TABLE_CONCEPT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONCEPT"
TABLE_SOLUTION = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION"
TABLE_SOURCE = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOURCE"





def normalize_llm_list(values):
    output = []

    for v in values or []:
        if not v:
            continue

        parts = re.split(r",|;", v)

        for p in parts:
            clean = p.strip()
            if clean:
                output.append(clean)

    return list(dict.fromkeys(output))

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
def destock_all_raw_contents(batch_size: int = 50):

    total_processed = 0
    total_errors = 0

    while True:

        result = destock_raw_contents(limit=batch_size)

        if result["total_selected"] == 0:
            break

        # 🔐 Sécurité anti-boucle infinie
        if result["processed"] == 0:
            print("Aucun traitement réussi dans ce batch → arrêt de sécurité")
            break

        total_processed += result["processed"]
        total_errors += result["errors"]

        print(
            f"Batch terminé → processed: {result['processed']} | errors: {result['errors']}"
        )

    return {
        "total_processed": total_processed,
        "total_errors": total_errors,
    }


# ============================================================
# DESTOCK RAW CONTENTS MOVE FROM SERVICE
# ============================================================

def destock_raw_contents(
    limit: int = 5,
    specific_id: Optional[str] = None
) -> Dict[str, Any]:

    # ====================================================
    # 1️⃣ SELECT RAW(S)
    # ====================================================

    if specific_id:

        raws = query_bq(
            f"""
            SELECT *
            FROM `{TABLE_CONTENT_RAW}`
            WHERE ID_RAW = @id_raw
            """,
            {"id_raw": specific_id}
        )

    else:

        raws = query_bq(
            f"""
            SELECT *
            FROM `{TABLE_CONTENT_RAW}`
            WHERE STATUS = 'STORED'
            ORDER BY CREATED_AT DESC
            LIMIT {limit}
            """
        )

    processed = 0
    errors = 0

    # ====================================================
    # 2️⃣ PROCESS LOOP
    # ====================================================

    for raw in raws:

        raw_id = raw["ID_RAW"]

        try:

            print("\n==============================")
            print("RAW ID:", raw_id)
            print("SOURCE_ID:", raw.get("SOURCE_ID"))

            # 🔥 NEW
            print(
                "ID_PRIMARY_COMPANY:",
                raw.get("ID_PRIMARY_COMPANY")
            )

            print("RAW LENGTH:", len(raw.get("RAW_TEXT", "") or ""))
            print("------------------------------")

            if raw["STATUS"] not in ["STORED", "ERROR"]:
                raise ValueError("RAW non traitable (status invalide)")

            # ====================================================
            # PASS TO PROCESSING
            # ====================================================

            update_bq(
                TABLE_CONTENT_RAW,
                {
                    "STATUS": "PROCESSING",
                    "ERROR_MESSAGE": None,
                },
                where={"ID_RAW": raw_id}
            )

            # 🔥 NEW
            id_primary_company = raw.get(
                "ID_PRIMARY_COMPANY"
            )

            # ====================================================
            # GENERATE CONTENT
            # ====================================================

            summary = generate_summary(
                source_id=raw.get("SOURCE_ID"),
                source_text=raw.get("RAW_TEXT", "")
            )

            concepts_llm = normalize_llm_list(
                summary.get("concepts", [])
            )

            solutions_llm = normalize_llm_list(
                summary.get("solutions", [])
            )

            topics_llm = normalize_llm_list(
                summary.get("topics", [])
            )

            acteurs_clean = normalize_llm_list(
                summary.get("acteurs_cites", [])
            )

            # ====================================================
            # CLEAN SOURCE_DATE
            # ====================================================

            raw_source_date = raw.get("DATE_SOURCE")

            source_date_clean = None

            if raw_source_date:

                if (
                    isinstance(raw_source_date, date)
                    and not isinstance(raw_source_date, datetime)
                ):

                    source_date_clean = raw_source_date

                elif isinstance(raw_source_date, datetime):

                    source_date_clean = raw_source_date.date()

                elif isinstance(raw_source_date, str):

                    try:

                        source_date_clean = datetime.strptime(
                            raw_source_date.split("T")[0],
                            "%Y-%m-%d"
                        )

                    except Exception:

                        source_date_clean = None

            # ====================================================
            # BUILD CONTENT MODEL
            # ====================================================

            content_payload = ContentCreate(

                # 🔥 NEW
                id_primary_company=id_primary_company,

                title=summary.get("title"),
                id_raw=raw.get("ID_RAW"),

                source_url=raw.get("SOURCE_URL"),

                source_title=raw.get("SOURCE_TITLE"),

                excerpt=summary.get("excerpt"),

                content_body=summary.get("content_body"),

                chiffres=summary.get("chiffres", []),

                acteurs_cites=summary.get("acteurs_cites", []),

                concepts_llm=concepts_llm,

                solutions_llm=solutions_llm,

                topics_llm=topics_llm,

                mecanique_expliquee=summary.get("mecanique_expliquee"),

                enjeu_strategique=summary.get("enjeu_strategique"),

                point_de_friction=summary.get("point_de_friction"),

                signal_analytique=summary.get("signal_analytique"),

                source_id=raw.get("SOURCE_ID"),

                source_date=source_date_clean,

                author=None,
            )

            content_id = create_content(content_payload)

            # ====================================================
            # MARK RAW AS PROCESSED
            # ====================================================

            update_bq(
                TABLE_CONTENT_RAW,
                {
                    "STATUS": "PROCESSED",
                    "PROCESSED_AT": datetime.utcnow(),
                    "GENERATED_CONTENT_ID": content_id,
                    "ERROR_MESSAGE": None,
                },
                where={"ID_RAW": raw_id}
            )

            processed += 1

        except Exception as e:

            print("\n❌ ERROR DURING DESTOCK:", str(e))

            update_bq(
                TABLE_CONTENT_RAW,
                {
                    "STATUS": "ERROR",
                    "ERROR_MESSAGE": str(e),
                },
                where={"ID_RAW": raw_id}
            )

            errors += 1

    return {
        "processed": processed,
        "errors": errors,
        "total_selected": len(raws),
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
# ============================================================
# SUBSTACK MOVE FROM SERVICE
# ============================================================

def raw_url_exists(url: str) -> bool:
    rows = query_bq(
        f"""
        SELECT 1
        FROM `{TABLE_CONTENT_RAW}`
        WHERE SOURCE_URL = @url
        LIMIT 1
        """,
        {"url": url},
    )
    return bool(rows)
